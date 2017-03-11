"""
Defines model fields designed to force field data types in the database.

Databases should be as self-documenting and semantic as possible, independent of
any application code, ORM models, or documentation. I will not compromise this
principle for the sake of an ORM's conveniences.

See:
    https://docs.djangoproject.com/en/dev/howto/custom-model-fields/

I have attempted to follow Google's Python style standards.

See:
    https://google.github.io/styleguide/pyguide.html?showone=Line_length#Line_length

"""

import datetime

import django.core.checks
import django.db.models
import django.db.utils


class FixedCharField(django.db.models.CharField):
    """
    Stores Python strings in fixed-length "char" database fields.

    Django's core CharField class saves all values in varchar data types
    with no option to use a char data type instead.

    CharField's max_length kwarg is kept for simplicity. In this class, the
    value of max_length will be the length of the char field.

    """

    def db_type(self, connection):
        """
        Override db_type().

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.db_type

        """
        return 'char({!s})'.format(self.max_length)


class TimestampField(django.db.models.DateTimeField):
    """
    Designed for use as a timezone-free system timestamp field.

    System timestamps are intended to record system-level events and moments in
    time. They contribute to database and record metadata.

    See:
        http://stackoverflow.com/a/410458

    MySQL/MariaDB supports the TIMESTAMP data type which includes special
    modifiers to ease its use as a system utility. These include the
    ON UPDATE CURRENT_TIMESTAMP modifier which essentially creates an implicit
    trigger. Django uses MySQL's DATETIME data type by default. This class uses
    MySQL's TIMESTAMP data type instead.

    Warning:
        When using the MySQL backend, the database TIMESTAMP field will also be
        updated when auto_now or auto_now_update is True and when calling
        QuerySet.update(). In constrast, Django's DateField and DateTimeField
        only set current timestamp under auto_now when calling Model.save().

    See:
        https://docs.djangoproject.com/en/dev/ref/models/fields/#datefield
        https://mariadb.com/kb/en/mariadb/timestamp/
        https://github.com/django/django/blob/master/django/db/backends/mysql/base.py

    PostgreSQL does not have anything resembling ON UPDATE CURRENT_TIMESTAMP
    aside from custom triggers. Django uses "timestamp with time zone" in its
    DateTimeField. However, its DATETIME equivalent data type "timestamp"
    does include the option to save without timezone. The explciit lack of
    timezone most closely aligns with the intended use case of this field class
    and is therefore used.

    See:
        https://www.postgresql.org/docs/current/static/datatype-datetime.html
        https://github.com/django/django/blob/master/django/db/backends/postgresql/base.py

    """

    def __init__(self, auto_now_update=False, *args, **kwargs):
        """
        Override the init method to add the auto_now_update keyword argument.

        Args:
            auto_now_update (boolean): When true, enables the automatic setting
                of the current timestamp on update operations only. Mutually
                exclusive with auto_now.

        """
        self._get_prep_value_add = None
        self.auto_now_update = auto_now_update
        super().__init__(*args, **kwargs)

    def _check_mutually_exclusive_options(self):
        """
        Override the mutual exclusivity check in parent class.

        django.db.models.fields.DateTimeCheckMixin is used to enforce mutual
        exclusivity between auto_now, auto_now_add, and default keyword
        arguments. This method also adds a check for auto_now_update and
        auto_now exclusivity.

        auto_now uses DEFAULT CURRENT_TIMESTAMP so auto_now and default are
        mutually exclusive. auto_now_add is mutually exclusive with auto_now
        since auto_now_add is a subset of auto_now functionality. The default
        The null option is independent except when False, in which case the
        default option may not be None.

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
            https://docs.djangoproject.com/en/dev/topics/checks/

        """
        # Checks auto_now, auto_now_add, and default mutual exclusivity.
        failed_checks = super()._check_mutually_exclusive_options()

        if self.auto_now and self.auto_now_update:
            failed_checks.append(
                django.core.checks.Error(
                    'The option auto_now is mutually exclusive with the option '
                    'auto_now_update.',
                    obj=self,
                    id=__name__ + '.E160'))

        return failed_checks

    def _db_type_mysql(self):
        """
        Assemble the db_type string for the MySQL backend.

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
            type_spec.append("DEFAULT '" + str(self.get_default()) + "'")

        if self.auto_now_update:
            # CURRENT_TIMESTAMP on update only.
            # Mutual exclusivity between auto_now and auto_now_update has
            # already been ensured by this point.
            type_spec.append(ts_default_on_update)

        if len(type_spec) == 1:
            # Disable default behavior if no special kwargs passed.
            if self.null:
                type_spec.append('DEFAULT NULL')
            else:
                type_spec.append('DEFAULT 0')

        return ' '.join(type_spec)

    def _db_type_postgresql(self):
        """
        Assemble the db_type string for the PostgreSQL backend.

        Returns:
            string: The db_type field definition string.

        """
        type_spec = ['TIMESTAMP WITHOUT TIME ZONE']
        if self.auto_now or self.auto_now_add:
            # CURRENT_TIMESTAMP on create
            type_spec.append('DEFAULT CURRENT_TIMESTAMP')
        elif self.has_default():
            # Set specified default on creation, no ON UPDATE action.
            # PostgreSQL uses double quotes only for system identifiers.
            type_spec.append("DEFAULT '" + str(self.get_default()) + "'")
        return ' '.join(type_spec)

    def _db_type_sqlite(self):
        """
        Assemble the db_type string for the sqlite3 backend.

        Returns:
            string: The db_type field definition string.

        """
        type_spec = ['DATETIME']
        if self.auto_now or self.auto_now_add:
            type_spec.append('DEFAULT CURRENT_TIMESTAMP')
        elif self.has_default():
            type_spec.append("DEFAULT '" + str(self.get_default()) + "'")
        return ' '.join(type_spec)

    def db_type(self, connection):
        """
        Override the db_type method.

        As of MySQL 5.7 and MariaDB 10.1, TIMESTAMP fields are defaulted to
        DEFAULT CURRENT_TIMESTAMP and ON UPDATE CURRENT_TIMESTAMP on table
        creation. In MySQL/MariaDB, NULL, DEFAULT, and ON UPDATE are not
        mutually exclusive on a TIMESTAMP field.

        See:
            https://dev.mysql.com/doc/refman/en/timestamp-initialization.html
            https://mariadb.com/kb/en/mariadb/timestamp/

        Type spec additions for self.null are not needed. Django magically
        appends NULL or NOT NULL to the end of the generated SQL. I'd look in
        the base Field class for that or in the backend-specific SQL compilers.

        Note that returning None from this method will cause Django to simply
        skip this field in its generated CREATE TABLE statements. This allows
        one to define the field manually and for Django to "get out of the way."

        In field deconstruction, Django's Field class uses the values from an
        instance's attributes rather than the passed **kwargs dict.

        See:
            https://github.com/django/django/blob/master/django/db/models/fields/__init__.py
            https://docs.djangoproject.com/en/dev/howto/custom-model-fields/#useful-methods

        """
        engine = connection.settings_dict['ENGINE']
        if engine == 'django.db.backends.mysql':
            db_type = self._db_type_mysql()
        elif engine == 'django.db.backends.postgresql':
            db_type = self._db_type_postgresql()
        elif engine == 'django.db.backends.sqlite3':
            db_type = self._db_type_sqlite()
        else:
            db_type = super().db_type(connection)

        return db_type

    def deconstruct(self):
        """
        Override the deconstruct method.

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.deconstruct

        """
        name, path, args, kwargs = super().deconstruct()
        if self.auto_now_update:
            kwargs['auto_now_update'] = True
        return (name, path, args, kwargs)

    def get_db_prep_save(self, value, connection):
        """
        MySQL, in typical fashion, presents an exception to the rule. When
        a TIMESTAMP field with no DEFAULT (including DEFAULT CURRENT_TIMESTAMP)
        and that is NOT NULL receives a NULL value on record INSERT or UPDATE,
        it is simply given the default value of zero which results in the
        timestamp 0000-00-00 00:00:00.

        In addition, the other database systems PostgreSQL and sqlite3
        rightfully raise exceptions in the aforementioned condition, citing
        integrity or constraint violations.

        This method override attempts to normalize MySQL's anomalous behavior in
        these situations by explicitly raising the same exception as the other
        Django backends. The exception message was copied from that of the other
        backends but I may need to be write a more specific one.

        See:
            https://dev.mysql.com/doc/refman/en/timestamp-initialization.html

        """
        add = self._get_prep_value_add
        self._get_prep_value_add = None

        engine = connection.settings_dict['ENGINE']

        # pylint doesn't like this conditional indent style but it is consistent
        # with Google style and I like it. Leave it alone.
        # Interested in finding config for pylint that will account for this.
        # https://google.github.io/styleguide/pyguide.html?showone=Line_length#Line_length
        if (engine == 'django.db.backends.mysql' and add and not self.null
            and value is None):
            raise django.db.utils.IntegrityError('NOT NULL constraint failed.')

        return super().get_db_prep_save(value, connection)

    def pre_save(self, model_instance, add):
        """
        Add auto_now_update to parent class' pre_save() implementation.

        I would like to implement this so that if an explcitly-assigned value
        exists on the model attribute, it will disable automatic setting of the
        datetime. This may be a future feature. On the other hand, that behavior
        can be largely emulated by setting "default" kwarg to a callable that
        returns datetime.datetime.today() and setting all auto_now options to
        False.

        Previously, I had attempted to avoid setting a current datetime value
        from within the ORM layer, instead allowing the DB engine to set it
        using database functions such as NOW() or keywords such as
        CURRENT_TIMESTAMP.

        Unfortunately, as is often the case, the ORM contains a limitation in
        that any and all output by get_db_prep_value() is quoted in the final,
        compiled SQL string output by the ORM. PostgreSQL and sqlite3
        interpreted NOW() as a function even surrounded by quotes but MySQL did
        not. I can find no way to disable the quoting of get_db_prep_value()
        output from within a custom field class and so must rely on the ORM
        layer datetime value overrides.

        I'm going to save my previous implementation here for easy retrieval in
        case I discover a solution to the quote problem. Most logic was handled
        in get_db_prep_value.

        Example:
            self._get_prep_value_add = add
            return super(django.db.models.DateField, self).pre_save(
                model_instance,
                add)

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.pre_save

        """
        self._get_prep_value_add = add

        # pylint doesn't like this conditional indent style but it is consistent
        # with Google style and I like it. Leave it alone.
        # https://google.github.io/styleguide/pyguide.html?showone=Line_length#Line_length
        if (self.auto_now or (self.auto_now_update and not add)
            or (self.auto_now_add and add)):
            value = datetime.datetime.today()
            setattr(model_instance, self.attname, value)
        else:
            # This super() call is correct. Leave it alone.
            # Skips DateTimeField and DateField pre_save() overrides while
            # maintaining binding to current class instance.
            # See: https://docs.python.org/3/library/functions.html#super
            value = super(django.db.models.DateField, self).pre_save(
                model_instance, add)

        return value

    def get_db_prep_value(self, value, connection, prepared=False):
        """
        Generate the raw output value for SQL compiler.

        self.default is handled by the base Field class. If no model attribute
        value is set and no default value is explicitly set, then the field
        default is None or empty string.

        As mentioned previously, the return value of this method is quoted in
        the compile SQL string. Until I find a way around this and can allow the
        current datetime to be set by the database instead of the ORM, I must
        rely upon pre_save() for the current datetime. My previous method
        definition will remain intact for the time being.

        This is very likely an incomplete implementation and has not been fully
        tested. It is saved here for a short time in case a solutiion is found
        to Django ORM automatically adding quotes around the value returned by
        this method. See the doc block for this class' pre_save() method.

        See:
            https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.get_db_prep_value
        """
        #add = self._get_prep_value_add
        #self._get_prep_value_add = None

        #needs_datetime_formatting = True

        #if not prepared:
            #prepared_value = None

            #engine = connection.settings_dict['ENGINE']
            #add_value_req = (self.auto_now or self.auto_now_add) and add \
                #and value is None
            #update_value_req = (self.auto_now or self.auto_now_update) \
                #and not add and value is None

            #if add_value_req or update_value_req:
                #if engine == 'django.db.backends.mysql':
                    #prepared_value = "CURRENT_TIMESTAMP"
                #elif engine == 'django.db.backends.postgresql':
                    #prepared_value = 'NOW()'
                #elif engine == 'django.db.backends.sqlite3':
                    #prepared_value = "datetime('now')"
                #needs_datetime_formatting = False

        #if needs_datetime_formatting:
            #prepared_value = super().get_db_prep_value(
                #value,
                #connection,
                #prepared)

        #return prepared_value

        return super().get_db_prep_value(value, connection, prepared)
