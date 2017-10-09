"""
Utility and common functions used in testing.

Since multiple database configs are defined in the settings.py and are being simultaneously tested,
a series of class constants are defined here, each containing the value of its respective DATABASES
alias. This makes it more explicit and readable which test is using what database and when.

If memory serves, the Django test classes attempt to use the DATABASES alias' NAME parameter for the
test database name suffix. Since there are no NAME parameters in the tests.settings module, the
suffix is empty, resulting in "test_".

"""

import datetime
import inspect
import re
import sys

import django.db.models
import django.db.utils
import django.utils.timezone


# Utilities to assist with referencing DATABASES settings dictionary.
#
# Originally, I attempted to leave the "default" DATABASES alias empty and to define each database
# by a non-default, explicit alias. However, despite my use of database routers, the Django TestCase
# still produced an error when tearing down the test case when the "default" alias was empty. The
# Django bug report below describes the error. For now, I'm just going to set "default" to point to
# the MySQL service instance as I'm tired of fighting with Django over anything remotely unusual in
# the way I want to structure my code.
#
# See:
# https://code.djangoproject.com/ticket/25504
# https://docs.djangoproject.com/en/dev/topics/db/multi-db/
# https://github.com/django/django/blob/master/django/core/management/commands/inspectdb.py
ALIAS_MYSQL = 'default'
ALIAS_POSTGRESQL = 'postgresql'
ALIAS_SQLITE = 'sqlite3'


def get_db_aliases():
    """
    Return a list of all DATABASES setting aliases in use in these tests.

    Recall that inspect.getmembers() returns a tuple of member (name, value).

    Returns:
        list: A sequence of database alias strings, NOT the name of this
            module's constant attribute.

    """

    return [
        member[1] for member
        in inspect.getmembers(sys.modules[__name__])
        if member[0].startswith('ALIAS_')
    ]


# Utilities to assist with timestamp field testing.
class TimestampFieldTestConfig:
    """
    A simple class to help centralize and organize test configs.

    A named tuple might also serve this purpose but I'm currently of the opinion that a small class
    is more explicit, cleaner, and more easily documented.

    For each valid combination of keyword arguments passed to the timestamp field, there is a
    corresponding set of expected outputs including the output of the customer field's db_type()
    method, the values it ultimately saves in the database, and other internal field class states.
    This class collects each associated set of inputs and outputs for easier testing.

    It is not necessary to test invalid model field attribute values as attribute value validation
    is already specifically tested in a test case.

    See:
        https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.db_type

    """

    def __init__(self, *, kwargs_dict, db_type_mysql, db_type_postgresql, insert_values_dict):
        """
        Args:
            kwargs_dict (dict): A dictionary of the k/v pairs to be passed as keyword arguments to
                the custom field constructor.
            db_type_mysql (str): The expected output of db_type() for the MySQL backend.
            db_type_postgresql (str): The expected output of db_type() for the PostgreSQL
                backend.
            insert_values_dict (dict): A dictionary of test input values (keys) and the resulting
                values that are expected to be retrieved from the database (values) after new record
                insert.

        See:
            https://www.python.org/dev/peps/pep-3102/

        """
        self.kwargs_dict = kwargs_dict
        self.db_type_mysql = db_type_mysql
        self.db_type_postgresql = db_type_postgresql
        self.insert_values_dict = insert_values_dict


_DEFAULT_DATETIME = datetime.datetime.now().replace(microsecond=0)
_DEFAULT_DATETIME_STR = str(_DEFAULT_DATETIME)
TS_FIELD_TEST_ATTRNAME = 'ts_field_1'
TS_FIELD_TEST_CONFIGS = [
    TimestampFieldTestConfig(
        kwargs_dict={},
        db_type_mysql='TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: django.db.utils.IntegrityError,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'null': True},
        db_type_mysql='TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now': True},
        db_type_mysql='TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _DEFAULT_DATETIME: datetime.datetime
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now': True, 'null': True},
        db_type_mysql='TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _DEFAULT_DATETIME: datetime.datetime
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_add': True},
        db_type_mysql='TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _DEFAULT_DATETIME: datetime.datetime
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_add': True, 'auto_now_update': True},
        db_type_mysql='TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _DEFAULT_DATETIME: datetime.datetime
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_add': True, 'auto_now_update': True, 'null': True},
        db_type_mysql='TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _DEFAULT_DATETIME: datetime.datetime
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_add': True, 'null': True},
        db_type_mysql='TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _DEFAULT_DATETIME: datetime.datetime
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_update': True},
        db_type_mysql='TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: django.db.utils.IntegrityError,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_update': True, 'null': True},
        db_type_mysql='TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_update': True, 'default': _DEFAULT_DATETIME},
        db_type_mysql='TIMESTAMP DEFAULT \'' + _DEFAULT_DATETIME_STR + '\' ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _DEFAULT_DATETIME_STR + "'",
        insert_values_dict={
            django.db.models.NOT_PROVIDED: _DEFAULT_DATETIME,
            None: django.db.utils.IntegrityError,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'auto_now_update': True, 'default': _DEFAULT_DATETIME, 'null': True},
        db_type_mysql='TIMESTAMP DEFAULT \'' + _DEFAULT_DATETIME_STR + '\' ON UPDATE CURRENT_TIMESTAMP',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _DEFAULT_DATETIME_STR + "'",
        insert_values_dict={
            django.db.models.NOT_PROVIDED: _DEFAULT_DATETIME,
            None: None,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'default': _DEFAULT_DATETIME},
        db_type_mysql='TIMESTAMP DEFAULT \'' + _DEFAULT_DATETIME_STR + '\'',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _DEFAULT_DATETIME_STR + "'",
        insert_values_dict={
            django.db.models.NOT_PROVIDED: _DEFAULT_DATETIME,
            None: django.db.utils.IntegrityError,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'default': _DEFAULT_DATETIME, 'null': True},
        db_type_mysql='TIMESTAMP DEFAULT \'' + _DEFAULT_DATETIME_STR + '\'',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _DEFAULT_DATETIME_STR + "'",
        insert_values_dict={
            django.db.models.NOT_PROVIDED: _DEFAULT_DATETIME,
            None: None,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    ),
    TimestampFieldTestConfig(
        kwargs_dict={'default': None, 'null': True},
        db_type_mysql='TIMESTAMP DEFAULT NULL',
        db_type_postgresql='TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL',
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            _DEFAULT_DATETIME: _DEFAULT_DATETIME
        }
    )
]
UPDATE_FIELD_TEST_ATTRNAME = 'update_field_1'


def get_ts_model_class_name(**kwargs):
    """
    Create a string for use as a dynamic class name.

    When testing all permutations of field keyword arguments in model classes, this function is used
    with the built-in function type() to dynamically generate the new model class' unique name.
    Subsequently, this function is called by the test suites to detrministically return a specific
    model class name based on desired field class configuration (kwargs). See sample usage of this
    function in the tests.models module.

    This algorithm is somewhat brittle. Not sure I like it.

    Args:
        kwargs: The keyword args that would be passed to the field in the test model class.

    See:
        https://docs.python.org/3/library/functions.html#type

    """
    kwargs_strings = []
    for key, value in kwargs.items():
        key_string = str(key).replace('_', '').title()
        if isinstance(value, datetime.datetime):
            value_string = 'Datetime'
        else:
            value_string =  re.sub(r'[\s:\-\.]', '', str(value)).title()
        kwargs_strings.append(key_string + value_string)
    suffix = ''.join(kwargs_strings)
    return 'TsRecord' + suffix


class TemporaryMigration:
    """
    A context manager that handles the creation and destruction of a single model's temporary table.

    Entering the context manager starts a migration of the passed model to a temporary table. The
    table is destroyed on context block exit.

    The table is created with the TEMPORARY SQL keyword. This class was created in an attempt to
    counter the implicit transaction commits of DDL statements in MySQL/MariaDB. However, TEMPORARY
    tables' structure cannot be queried or examined through the information_schema database which
    breaks the database table structure tests. I could attempt to parse the output from a SHOW
    CREATE statement but the investment-to-return ratio is currently unfavorable.

    This functionality was defined as a context manager to ensure that the monkey-patching to
    the SQL compiler is inevitably reversed.

    Warning:
        This class is no longer used in the tests. I'm saving this for future reference and until
        I'm sure I won't need it. It also serves as a refresher for me on how the Django ORM
        internals work. This solution strikes me as clever but smelly.

    See:
        https://docs.python.org/3/reference/compound_stmts.html#the-with-statement

    """

    sql_editor_kwargs = {'atomic': True}
    sql_temporary = 'TEMPORARY'

    def __init__(self, connection, model):
        self._connection = connection
        self._model = model

    def __enter__(self):
        """
        Alter the ORM SQL compiler and migrate a model to a TEMPORARY table.

        self._connection.features.can_rollback_ddl == False in MySQL

        Note that BaseDatabaseSchemaEditor collect_sql = True bypasses actual execution and instead
        stores generated SQL in a list. This could be useful.

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/schema.py

        """
        with self._connection.schema_editor(**self.sql_editor_kwargs) as schema_editor:
            schema_editor.sql_create_table = (
                schema_editor.sql_create_table[:7]
                + self.sql_temporary
                + schema_editor.sql_create_table[6:]
            )
            schema_editor.create_model(self._model)

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Reverse ORM SQL compiler modifications and destroy the TEMPORARY table.

        """
        with self._connection.schema_editor(**self.sql_editor_kwargs) as schema_editor:
            schema_editor.sql_create_table = schema_editor.sql_create_table.replace(
                self.sql_temporary,
                ''
            )
            schema_editor.delete_model(self._model)
