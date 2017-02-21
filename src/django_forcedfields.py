"""
Defines model fields designed to force field data types in the database.

Databases should be as self-documenting and semantic as possible, independent of
any application code, ORM models, or documentation. I will not compromise this
principle for the sake of an ORM's conveniences.

See:
    https://docs.djangoproject.com/en/dev/howto/custom-model-fields/

"""

from django.db import models


class FixedCharField(models.CharField):
    """
    Stores Python strings in fixed-length "char" database fields.

    CharField's max_length kwarg is kept for simplicity. In this class, the
    value of max_length will be the length of the char field.

    """

    def db_type(self, connection):
        #if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
            #db_type = super().db_type(connection)
        #else:
            #db_type = 'char({!s})'.format(self.max_length)
        return 'char({!s})'.format(self.max_length)


class TimestampField(models.DateTimeField):
    """
    Designed for use as a timezone-free system timestamp field.

    MySQL/MariaDB uses the TIMESTAMP data type which includes special modifiers
    to ease its use as a system utility.

    According to PEP 8, this class name could contain capitalized
    "abbreviations" (MariaDB instead of Mariadb) but MariaDB isn't an acronym
    such as HTTP and I prefer to maintain the demarkation of words within the
    name. "MariaDB" could potentially suggest that Maria and DB are separate
    parts.

    See:
        https://www.python.org/dev/peps/pep-0008/#descriptive-naming-styles

    """

    def db_type(self, connection):
        """
        The DateField/DateTimeField enforces mutual exclusivity between
        auto_now, auto_now_add, and default. Check is performed between call to
        db_type and the generation of actual SQL string. Therefore, these
        conflicting instance attributes cannot even be set internally here.

        As of MySQL 5.7 and MariaDB 10.1, TIMESTAMP fields are defaulted to
        auto-update with CURRENT_TIMESTAMP on creation and update of record.

        In MySQL/MariaDB, NULL, DEFAULT, and ON UPDATE are not mutually
        exclusive on a TIMESTAMP field.

        See:
            https://dev.mysql.com/doc/refman/5.7/en/timestamp-initialization.html
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
                # self.default = 'CURRENT_TIMESTAMP'
                type_spec.extend([ts_default_default, ts_default_on_update])
            elif self.auto_now_add:
                # CURRENT_TIMESTAMP on create only.
                # self.default = 'CURRENT_TIMESTAMP'
                type_spec.append(ts_default_default)
            elif self.has_default():
                # Set specified default on creation, no ON UPDATE action.
                type_spec.append('DEFAULT ' + str(self.default))
            elif not self.null:
                # Disable all default bahavior.
                self.default = 0
            db_type = ' '.join(type_spec)
        else:
            db_type = super().db_type(connection)

        return db_type
