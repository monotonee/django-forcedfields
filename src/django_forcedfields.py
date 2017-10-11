"""
Defines custom Django ORM model fields designed to force field data types in the database.

Databases should be as self-documenting and semantic as possible, independent of any application
code, ORM models, or documentation. To that end, this module aims to force the ORM to conduct more
explicit database operations and to shift duties from the application to the database where
appropriate and consistent with best practices.

Django's documentation concerning the creation of custom model fields is cursory and unclear and the
method names are needlessly vague. As I understand it, the following is a very rough overview of the
flow of Field API method calls in order starting with fetching data FROM the database and ending
with returning data TO the database:

    1. from_db_value
    2. to_python
        - "Convert the input value into the expected Python data type"
        - Usually not called by the SQL compilers directly. Used internally by the Field classes.
    3. pre_save
        - "Return field's value just before saving."
        - Called by the SQL compilers to fetch the value of the model's field attribute for the
            first time before eventually being passed to the Field's *_prep_value() methods.
        - See source for django.db.models.sql.SQLCompiler.pre_save_val()
    4. get_prep_value
        - "Perform preliminary non-db specific value checks and conversions."
        - Seems to be used internally by the Field classes. Doesn't seem to be called directly by
            SQL compilers.
    5. get_db_prep_value
        - "Return field's value prepared for interacting with the database backend."
        - Seems to be used internally by the Field classes. Doesn't seem to be called directly by
            SQL compilers.
        - For example, this is called by base Field class' get_db_prep_save().
    6. get_db_prep_save
        - "Return field's value prepared for saving into a database."
        - Called directly by SQL compilers.
        - See source for django.db.models.sql.SQLCompiler.prepare_value().
        - Called in django.db.models.sql.compiler.SQLInsertCompiler.prepare_value()

See:
    https://docs.djangoproject.com/en/dev/howto/custom-model-fields/
    https://docs.djangoproject.com/en/dev/ref/models/fields/#field-api-reference
    https://github.com/django/django/blob/master/django/db/models/fields/__init__.py
    https://github.com/django/django/blob/master/django/db/models/sql/compiler.py

I have attempted to follow PEP8 styles, supplemented by Google's Python style standards. Some PEP8
standards are rather arcane such as 79-character maximum line length. In this and similar cases, I
defer to Google's style guide. I use Google's doc block and inline comment formatting standards.

See:
    https://google.github.io/styleguide/pyguide.html?showone=Line_length#Line_length

"""

import django.core.checks
import django.db.models
import django.db.models.functions
import django.db.utils


class FixedCharField(django.db.models.CharField):
    """
    A custom Django ORM field class that stores values in fixed-length "char" database fields.

    Django's core CharField class saves all values in varchar data types with no option to use a
    char data type instead.

    CharField's max_length kwarg is kept for simplicity. In this class, the value of max_length will
    be the length of the char field.

    """

    def db_type(self, connection):
        """
        Override db_type().

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.db_type

        """
        return 'CHAR({!s})'.format(self.max_length)


class TimestampField(django.db.models.DateTimeField):
    """
    A custom Django ORM field class designed for use as a timezone-free system timestamp field.

    System timestamps are intended to record system-level events and moments in time. They
    contribute to database and record metadata.

    See:
        http://stackoverflow.com/a/410458

    MySQL/MariaDB supports the TIMESTAMP data type which includes special modifiers to ease its use
    as a system utility. These include the ON UPDATE CURRENT_TIMESTAMP modifier which essentially
    creates an implicit trigger. Django uses MySQL's DATETIME data type by default while this class
    overrides this and uses MySQL's TIMESTAMP data type instead.

    Warning:
        When using the MySQL backend, the database TIMESTAMP field will also be updated when
        auto_now or auto_now_update is True and when calling QuerySet.update(). In constrast,
        Django's DateField and DateTimeField only set current timestamp under auto_now when calling
        Model.save().

    See:
        https://docs.djangoproject.com/en/dev/ref/models/fields/#datefield
        https://mariadb.com/kb/en/mariadb/timestamp/
        https://github.com/django/django/blob/master/django/db/backends/mysql/base.py

    PostgreSQL does not have anything resembling ON UPDATE CURRENT_TIMESTAMP aside from custom
    triggers. However, its equivalent of MySQL's DATETIME data type is "timestamp", which does
    include the option to save without timezone. This explciit lack of timezone most closely aligns
    with the intended use case of this field class and is therefore used.

    See:
        https://www.postgresql.org/docs/current/static/datatype-datetime.html
        https://github.com/django/django/blob/master/django/db/backends/postgresql/base.py

    """

    def __init__(self, *args, auto_now_update=False, **kwargs):
        """
        Override the init method to add the auto_now_update keyword argument.

        Args:
            auto_now_update (boolean): When true, enables the automatic setting of the current
                timestamp on update operations only. Mutually exclusive with auto_now.

        """
        self.auto_now_update = auto_now_update
        super().__init__(*args, **kwargs)

    def _check_mutually_exclusive_options(self):
        """
        Override the mutual exclusivity check in parent class.

        django.db.models.fields.DateTimeCheckMixin is used to enforce mutual exclusivity between
        auto_now, auto_now_add, and default keyword arguments. This method also adds a check for
        auto_now_update and auto_now exclusivity.

        auto_now, auto_now_add, and default all logically define a DEFAULT clause and are therefore
        mutually exclusive. auto_now logically defines DEFAULT and ON UPDATE clauses and is
        therefore mutually exclusive with auto_now_add (DEFAULT) and auto_now_update (ON UPDATE).

        Valid permutations:
            <empty set>
            null
            auto_now
            auto_now + null
            auto_now_add
            auto_now_add + auto_now_update
            auto_now_add + auto_now_update + null
            auto_now_add + null
            auto_now_update
            auto_now_update + null
            default
            default + auto_now_update
            default + auto_now_update + null
            default + null

        Returns:
            list: A list of additional Django check messages.

        See:
            https://github.com/django/django/blob/master/django/db/models/fields/__init__.py
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.DateField
            https://docs.djangoproject.com/en/dev/topics/checks/

        """
        # Checks auto_now, auto_now_add, and default mutual exclusivity.
        failed_checks = super()._check_mutually_exclusive_options()

        if self.auto_now and self.auto_now_update:
            failed_checks.append(
                django.core.checks.Error(
                    'The option auto_now is mutually exclusive with the option auto_now_update.',
                    obj=self,
                    id=__name__ + '.E160'
                )
            )

        return failed_checks

    def _db_type_mysql(self, connection):
        """
        Assemble the db_type string for the MySQL backend.

        Note that in MySQL, if no DEFAULT or ON UPDATE clauses are specified for a TIMESTAMP field
        in a CREATE TABLE statement, certain DEFAULT CURRENT_TIMESTAMP and ON UPDATE
        CURRENT_TIMESTAMP values are automatically applied depending upon server configuration.
        Enable the "explicit_defaults_for_timestamp" server system variable to disable this. See
        README for more details.

        At minimum, a DEFAULT clause must be specified in order to be compatible with MySQL server
        system variable explicit_defaults_for_timestamp. MySQL strict mode, NO_ZERO_DATE,
        NO_ZERO_IN_DATE, and explicit_defaults_for_timestamp all affect what values and defaults are
        valid and it is the user's responsibility to effect the desired database behavior by setting
        these configurations on the database server. See README and your database engine's
        documentation for more details.

        See:
            https://dev.mysql.com/doc/refman/en/timestamp-initialization.html
            https://dev.mysql.com/doc/refman/en/server-system-variables.html#sysvar_explicit_defaults_for_timestamp
            https://jira.mariadb.org/browse/MDEV-10802

        I'm concerned about outputting the DEFAULT clause here. The Django schema editor mechanism
        already seems to provide a way to output DEFAULT although it doesn't appear to be used in
        core and it appears narrow in scope. Default values are (sigh) usually applied in the
        application layer in a model's __init__ method if no field value was explicitly defined in
        model's initial kwargs.

        See:
            https://github.com/django/django/blob/master/django/db/models/base.py
            https://github.com/django/django/blob/master/django/db/backends/base/schema.py
                django.db.backends.base.BaseDatabaseSchemaEditor.column_sql
                django.db.backends.base.BaseDatabaseSchemaEditor.create_model

        Args:
            connection: The Django connection object that was passed to the db_type() override.

        Returns:
            string: The db_type field definition string.

        """
        type_spec = ['TIMESTAMP']
        ts_default_default = 'DEFAULT CURRENT_TIMESTAMP'
        ts_default_on_update = 'ON UPDATE CURRENT_TIMESTAMP'
        if self.auto_now:
            # CURRENT_TIMESTAMP on create and on update.
            type_spec.extend([ts_default_default, ts_default_on_update])
        elif self.auto_now_add:
            # CURRENT_TIMESTAMP on create only.
            type_spec.append(ts_default_default)
        elif self.has_default():
            # Set specified default on creation, no ON UPDATE action.
            default_value = self._get_prep_default_value(self.get_default(), connection)
            type_spec.append('DEFAULT {!s}'.format(default_value))

        if self.auto_now_update:
            # CURRENT_TIMESTAMP on update only.
            # Mutual exclusivity between auto_now and auto_now_update has already been ensured by
            # self._check_mutually_exclusive_options() by the time this method has been called.
            type_spec.append(ts_default_on_update)

        return ' '.join(type_spec)

    def _db_type_postgresql(self, connection):
        """
        Assemble the db_type string for the PostgreSQL backend.

        PostgreSQL has no equivalent to MySQL's ON UPDATE clause. Values on update are handled
        manually in the ORM layer. See pre_save().

        Args:
            connection: The Django connection object that was passed to the db_type() override.

        Returns:
            string: The db_type field definition string.

        """
        type_spec = ['TIMESTAMP WITHOUT TIME ZONE']
        if self.auto_now or self.auto_now_add:
            # CURRENT_TIMESTAMP on create
            type_spec.append('DEFAULT CURRENT_TIMESTAMP')
        elif self.has_default():
            # Set specified default on creation, no ON UPDATE action.
            # Warning: PostgreSQL uses double quotes only for system identifiers.
            default_value = self._get_prep_default_value(self.get_default(), connection)
            type_spec.append('DEFAULT {!s}'.format(default_value))

        return ' '.join(type_spec)

    def _db_type_sqlite(self, connection):
        """
        Assemble the db_type string for the sqlite3 backend.

        SQLite has no equivalent to MySQL's ON UPDATE clause. Values on update are handled
        manually in the ORM layer. See pre_save().

        Args:
            connection: The Django connection object that was passed to the db_type() override.

        Returns:
            string: The db_type field definition string.

        """
        type_spec = ['DATETIME']
        if self.auto_now or self.auto_now_add:
            type_spec.append('DEFAULT CURRENT_TIMESTAMP')
        elif self.has_default():
            default_value = self._get_prep_default_value(self.get_default(), connection)
            type_spec.append('DEFAULT {!s}'.format(default_value))

        return ' '.join(type_spec)

    def _get_prep_default_value(self, value, connection):
        """
        Generate a SQL DEFAULT clause value for use in a column DDL statement.

        This is not intended to be universal to any model field class. Rather, it is only designed
        to handle the use case of TIMESTAMP field types. "None" values will be converted to NULL and
        all other values will be passed to the parent's get_prep_value() where a valid datetime
        value will attempt to be parsed out.

        Default values in Django's ORM are (sigh) usually applied in the application layer in a
        model's __init__ method if no field value was explicitly defined in model's initial kwargs.
        This method is responsible for creating a valid default value to be issued to a DB engine
        in the column's DDL SQL. There is currently no need to differentiate DEFAULT values by DB
        engine.

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#default

        Note that the parent DateTimeField/DateField can raise validation errors in the model.save()
        call without having called full_clean(). ValidationErrors are raised in
        DateTimeField.to_python() which is called by DateTimeField.get_prep_value() (on save) and by
        the model's clean methods (full_clean(), etc.). Apparently, to_python() is the "first step
        in every validation." Therefore, ValidationError may be raised from this method since it
        calls the parent's get_db_prep_value() method which ultimately calls to_python() in the
        attempt to parse a datetime value.

        See:
            https://docs.djangoproject.com/en/dev/ref/forms/validation/
            https://docs.djangoproject.com/en/dev/ref/models/instances/#validating-objects
            https://github.com/django/django/blob/master/django/utils/dateparse.py
            https://github.com/django/django/blob/master/django/db/models/fields/__init__.py
                django.db.models.fields.DateTimeField.get_prep_value()

        Args:
            value: The desired value of the field class' "default" kwarg and instance attribute.
            connection: The Django connection object that was passed to db_type().

        Returns:
            str: A valid SQL DEFAULT value usable in a column's DDL statement.

        Raises:
            ValidationError: If the passed default value cannot be converted into a valid DDL value.

        """
        default_value_prepared = value

        if value is None:
            default_value_prepared = 'NULL'
        else:
            # Will raise ValidationError for invalid datetime values.
            # Underlying django.utils.dateparse.parse_date() expects and requires a string.
            # get_db_prep_value() is used instead of to_python() since DB-specific datetime formats
            # are necessary for the DEFAULT clause value.
            default_value_prepared = super().get_db_prep_value(
                str(value),
                connection,
                prepared=False
            )
            default_value_prepared = "'{!s}'".format(default_value_prepared)

        return default_value_prepared

    def db_type(self, connection):
        """
        Override the db_type method.

        Type spec additions for self.null are not needed. Django magically appends NULL or NOT NULL
        to the end of the generated SQL.

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/schema.py
                BaseDatabaseSchemaEditor.column_sql

        Note that returning None from this method will cause Django to simply skip this field in its
        generated CREATE TABLE statements. This allows one to define the field manually outside of
        the ORM, a feature that may prove useful in the future.

        See:
            https://github.com/django/django/blob/master/django/db/models/fields/__init__.py
            https://docs.djangoproject.com/en/dev/howto/custom-model-fields/#useful-methods

        """
        engine = connection.settings_dict['ENGINE']
        if engine == 'django.db.backends.mysql':
            db_type = self._db_type_mysql(connection)
        elif engine == 'django.db.backends.postgresql':
            db_type = self._db_type_postgresql(connection)
        elif engine == 'django.db.backends.sqlite3':
            db_type = self._db_type_sqlite(connection)
        else:
            db_type = super().db_type(connection)

        return db_type

    def deconstruct(self):
        """
        Override the deconstruct method to ensure auto_now_update value is preserved.

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.deconstruct

        """
        name, path, args, kwargs = super().deconstruct()
        if self.auto_now_update:
            kwargs['auto_now_update'] = True
        return (name, path, args, kwargs)

    def pre_save(self, model_instance, add):
        """
        Set current timestamp if auto_now_update option is active.

        If an auto_now, auto_now_add, or auto_now_update condition is active, override the field
        value with current timestamp. This may not reflect underlying DB behavior in which explicit
        values override DEFAULT and ON UPDATE, but it remains consistent with parent DateTimeField
        behavior.

        The model's attribute value will be set to a Django Func() expression when an auto_now*
        condition is active. Given the common use cases of the auto_now* options, I deem this
        acceptable as historically, one would expect automatic timestamps to be generated in the
        database instead of the application.

        The only other options are to set the model attribute to a Python datetime value and hope
        that it is not too different from the value that the database generated or to issue a second
        query after successful save to retrieve the generated current timestamp.

        For future reference, note that in the parent DateTimeField, date parse validation is
        triggered by SQL compiler through get_db_prep_save(), get_db_prep_value(), get_prep_value(),
        which finally calls to_python(), which in turn raises ValidationError if date parse fails.

        The SQL compiler (django.db.models.sql.compiler.SQLInsertCompiler) calls this method on
        fields to get the value to be inserted in the SQL insert VALUES list.

        See:
            https://github.com/django/django/blob/master/django/db/models/sql/compiler.py
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.pre_save

        """
        # Based on my review of Django source, I do not believe one can omit a value altogether for
        # a field in an INSERT or UPDATE SQL statement. The ModelBase.save() method seems to
        # indiscriminately sweep all fields into the insert process. Therefore, use explicit value.
        if self.auto_now or (self.auto_now_update and not add) or (self.auto_now_add and add):
            value = django.db.models.functions.Now()
            setattr(model_instance, self.attname, value)
        else:
            # This super() call is correct. Leave it alone.
            # Skips DateTimeField and DateField pre_save() overrides while maintaining binding to
            # current class instance.
            # See: https://docs.python.org/3/library/functions.html#super
            value = super(django.db.models.DateField, self).pre_save(model_instance, add) # pylint: disable=bad-super-call

        return value
