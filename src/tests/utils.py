"""
Utility and common functions used in testing.

Since multiple database configs are defined in the settings.py and are being
simultaneously tested, a series of class constants are defined here, each
containing the value of its respective DATABASES alias. This makes it more
explicit and readable which test is using what database and when.

If memory serves, the Django test classes attempt to use the DATABASES
alias' NAME parameter for the test database name suffix. Since there are no
NAME parameters in the tests.settings module, the suffix is empty, resulting
in "test_".

"""

import datetime
import inspect
import sys

import django.db

"""
Utilities to assist with referencing DATABASES settings dictionary.

"""
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
    return [member[1] for member
        in inspect.getmembers(sys.modules[__name__])
        if member[0].startswith('ALIAS_')]


"""
Utilities to assist with timestamp field testing.

"""
class TimestampFieldTestConfig:
    """
    A simple class to help centralize and organize test configs.

    A named tuple might also serve this purpose but i'm currently of the
    opinion that a small class is more explicit, cleaner, and more easily
    documented.

    For each valid combination of keyword arguments passed to the timestamp
    field, there is a corresponding set of expected outputs including the output
    of the customer field's db_type() method, the values it ultimately saves
    in the database, and other internal field class states. This class collects
    each associated set of inputs and outputs for easier testing.

    It is not necessary to test invalid modelfield attribute values as attribute
    value validation is already specifically tested in a test case.

    See:
        https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.db_type

    """

    def __init__(
        self, kwargs_dict, db_type_mysql, db_type_postgresql,
        save_values_dict=None):
        """
        Args:
            kwargs_dict (dict): A dictionary of the k/v pairs to be passed as
                keyword arguments to the custom field constructor.
            db_type_mysql (string): The expected output of db_type() for the
                MySQL backend.
            db_type_postgresql (string): The expected output of db_type() for
                the PostgreSQL backend.
            save_values_dict (dict): A dictionary of test input values (keys)
                and the resulting values that are expected to be stored in the
                database (values).

        """
        self.kwargs_dict = kwargs_dict
        self.db_type_mysql = db_type_mysql
        self.db_type_postgresql = db_type_postgresql
        self.save_values_dict = save_values_dict


_default_datetime = datetime.datetime.today().replace(microsecond=0)
_default_datetime_str = str(_default_datetime)
TS_FIELD_TEST_ATTRNAME = 'ts_field_1'
TS_FIELD_TEST_CONFIGS = [
    TimestampFieldTestConfig(
        {'auto_now': True},
        'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        {
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now': True, 'null': True},
        'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        {
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: None,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_add': True},
        'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        {
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_add': True, 'auto_now_update': True},
        'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        {
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_add': True, 'auto_now_update': True, 'null': True},
        'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        {
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: None,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_add': True, 'null': True},
        'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
        {
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: None,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_update': True},
        'TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE',
        {
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: django.db.utils.IntegrityError,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_update': True, 'null': True},
        'TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE',
        {
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: None,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_update': True, 'default': _default_datetime},
        'TIMESTAMP DEFAULT \'' + _default_datetime_str \
            + '\' ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _default_datetime_str + "'",
        {
            django.db.models.NOT_PROVIDED: _default_datetime,
            None: django.db.utils.IntegrityError,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'auto_now_update': True, 'default': _default_datetime, 'null': True},
        'TIMESTAMP DEFAULT \'' + _default_datetime_str \
            + '\' ON UPDATE CURRENT_TIMESTAMP',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _default_datetime_str + "'",
        {
            django.db.models.NOT_PROVIDED: _default_datetime,
            None: None,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'default': _default_datetime},
        'TIMESTAMP DEFAULT \'' + _default_datetime_str + '\'',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _default_datetime_str + "'",
        {
            django.db.models.NOT_PROVIDED: _default_datetime,
            None: django.db.utils.IntegrityError,
            _default_datetime: _default_datetime
        }),
    TimestampFieldTestConfig(
        {'default': _default_datetime, 'null': True},
        'TIMESTAMP DEFAULT \'' + _default_datetime_str + '\'',
        'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'' + _default_datetime_str + "'",
        {
            django.db.models.NOT_PROVIDED: _default_datetime,
            None: None,
            _default_datetime: _default_datetime
        })]


def get_ts_model_class_name(**kwargs):
    """
    Create a string for use as part of a dynamic class name.

    When testing all permutations of field keyword arguments in model classes,
    for instance, this function is used with the built-in function type() to
    dynamically generate the new model class' name.

    See usage of this function in the tests.models module.

    Args:
        kwargs: The keyword args that will be passed to the field in the test
            model class.

    See:
        https://docs.python.org/3/library/functions.html#type

    """
    suffix = ''.join([key.replace('_', '').title() for key in kwargs.keys()])
    return 'TsRecord' + suffix


class TemporaryMigration:
    """
    This class handles the creation and destruction of a single model's table.

    The table is created as TEMPORARY.

    I'm only saving this until I'm sure it isn't needed to complete tests.

    """

    sql_temporary = 'TEMPORARY'

    def __init__(self, connection, model):
        self._connection = connection
        self._model = model

    def __enter__(self):
        """
        self._connection.features.can_rollback_ddl == False in MySQL

        Note that BaseDatabaseSchemaEditor collect_sql = True bypasses actual
        execution and instead stores generated SQL in a list.

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/schema.py

        """
        #editor_kwargs = {
            #'atomic': True,
            #'collect_sql': True}
        editor_kwargs = {
            'atomic': True}
        with self._connection.schema_editor(**editor_kwargs) as schema_editor:
            schema_editor.sql_create_table = (
                schema_editor.sql_create_table[:7]
                + self.sql_temporary
                + schema_editor.sql_create_table[6:])
            schema_editor.create_model(self._model)

    def __exit__(self, exc_type, exc_value, traceback):
        with self._connection.schema_editor(**editor_kwargs) as schema_editor:
            schema_editor.sql_create_table = \
                schema_editor.sql_create_table.replace(self.sql_temporary, '')
            schema_editor.delete_model(self._model)
