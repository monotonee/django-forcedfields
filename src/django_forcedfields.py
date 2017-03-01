"""
Defines model fields designed to force field data types in the database.

Databases should be as self-documenting and semantic as possible, independent of
any application code, ORM models, or documentation. I will not compromise this
principle for the sake of an ORM's conveniences.

See:
    https://docs.djangoproject.com/en/dev/howto/custom-model-fields/

"""

import django.core.checks
from django.db import models


class FixedCharField(models.CharField):
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


class TimestampField(models.DateTimeField):
    """
    Designed for use as a timezone-free system timestamp field.

    System timestamps are intended to record system-level events and moments in
    time. They contribute to database and record metadata.

    See:
        https://stackoverflow.com/questions/409286/should-i-use-field-datetime-or-timestamp

    MySQL/MariaDB supports the TIMESTAMP data type which includes special
    modifiers to ease its use as a system utility. These include the
    CURRENT_TIMESTAMP keyword which allows the system to automatically set
    timestamp based on INSERT and/or UPDATE.

    Django uses MySQL's DATETIME data type by default. This class uses MySQL's
    TIMESTAMP data type instead. This field class will also disable Django's
    application-layer auto_now and auto_now_add behavior, allowing the database
    engine itself to handle automatic value creation and update.

    Warning:
        When using the MySQL backend, the database TIMESTAMP field will also be
        updated when auto_now is True and when calling QuerySet.update().
        Django's DateField and DateTimeField only set current timestamp under
        auto_now when calling Model.save().

    See:
        https://docs.djangoproject.com/en/dev/ref/models/fields/#datefield
        https://mariadb.com/kb/en/mariadb/timestamp/
        https://github.com/django/django/blob/master/django/db/backends/mysql/base.py

    PostgreSQL does not have anything resembling CURRENT_TIMESTAMP aside from
    custom triggers. Django uses "timestamp with time zone" in its
    DateTimeField. However, its DATETIME equivalent data type "timestamp"
    does include the option to save without timezone. This lack of timestamp
    most closely aligns with the intended use case of this field class and is
    therefore used.

    See:
        https://www.postgresql.org/docs/current/static/datatype-datetime.html
        https://github.com/django/django/blob/master/django/db/backends/postgresql/base.py

    According to PEP 8, this class name could contain capitalized
    "abbreviations" (MariaDB instead of Mariadb) but MariaDB isn't an acronym
    such as HTTP and I prefer to maintain the demarkation of words within the
    name.

    See:
        https://www.python.org/dev/peps/pep-0008/#descriptive-naming-styles

    """

    def __init__(self, auto_now_update=False, *args, **kwargs):
        """
        Override the init method to add the auto_now_update keyword argument.

        """
        self.auto_now_update = auto_now_update
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.auto_now_update:
            kwargs['auto_now_update'] = True
        return (name, path, args, kwargs)

    def _check_mutually_exclusive_options(self):
        """
        Override the mutual exclusivity check in parent class.

        django.db.models.fields.DateTimeCheckMixin is used to enforce mutual
        exclusivity between auto_now, auto_now_add, and default keyword
        arguments. This restriction doesn't make a lot of sense in light of
        MySQL's and Postgres' possible TIMESTAMP field combinations.

        auto_now uses DEFAULT CURRENT_TIMESTAMP so auto_now and default are
        mutually exclusive. auto_now_add is mutually exclusive with auto_now
        since auto_now_add is a subset of auto_now functionality. The default
        The null option is independent except when False, in which case the
        default option may not be None.

        Valid permutations:
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
            https://github.com/django/django/blob/master/django/db/models/fields/__init__.py#L1089
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

        # If null is False, I believe Django will simply attempt to store the
        # None default as an empty string.
        #if self.null and self.default == None:
            #failed_checks.append(
                #django.core.checks.Error(
                    #'If the option "default" is None, then the "null" option '
                    #'must be True.',
                    #obj=self))

        return failed_checks

    def db_type(self, connection):
        """
        The DateField/DateTimeField enforces mutual exclusivity between
        auto_now, auto_now_add, and default. Check is performed between call to
        db_type and the generation of actual SQL string. Therefore, these
        conflicting instance attributes cannot even be set manually in a custom
        field class.

        As of MySQL 5.7 and MariaDB 10.1, TIMESTAMP fields are defaulted to
        DEFAULT CURRENT_TIMESTAMP and ON UPDATE CURRENT_TIMESTAMP on table
        creation. In MySQL/MariaDB, NULL, DEFAULT, and ON UPDATE are not
        mutually exclusive on a TIMESTAMP field.

        Type spec additions for self.null are not needed. Django magically
        appends NULL or NOT NULL to the end of the generated SQL. I'd look in
        the base Field class for that.

        See:
            https://dev.mysql.com/doc/refman/en/timestamp-initialization.html
            https://mariadb.com/kb/en/mariadb/timestamp/

        In field deconstruction, Django's Field class uses the values from an
        instance's attributes rather than the passed **kwargs dict.

        See:
            https://github.com/django/django/blob/master/django/db/models/fields/__init__.py#L365

        """
        if connection.settings_dict['ENGINE'] == 'django.db.backends.mysql':
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
                type_spec.append('DEFAULT ' + str(self.default))

            if self.auto_now_update:
                # Mutual exclusivity between auto_now and auto_now_update has
                # already been ensured by this point.
                type_spec.append(ts_default_on_update)

            db_type = ' '.join(type_spec)
        else:
            db_type = super().db_type(connection)

        return db_type
