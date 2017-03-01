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

import inspect
import sys

# DATABASES settings keys (aliases).
ALIAS_MYSQL = 'default'
ALIAS_POSTGRESQL = 'postgresql'
ALIAS_SQLITE = 'sqlite3'

# Constants to assist with timestamp field testing.
TS_FIELD_TEST_ATTRNAME = 'ts_field_1'
TS_FIELD_TEST_KWARG_PERMUTATIONS = [
    {'auto_now': True},
    {'auto_now': True, 'null': True},
    {'auto_now_add': True},
    {'auto_now_add': True, 'auto_now_update': True},
    {'auto_now_add': True, 'auto_now_update': True, 'null': True},
    {'auto_now_add': True, 'null': True},
    {'auto_now_update': True},
    {'auto_now_update': True, 'null': True},
    {'auto_now_update': True, 'default': 0},
    {'auto_now_update': True, 'default': 0, 'null': True},
    {'default': 0},
    {'default': 0, 'null': True}]
TS_FIELD_TEST_PREFIX = 'TsRecord'


def get_db_aliases():
    """
    Return a list of all DATABASES setting aliases in use in these tests.

    Recall that inspect.getmembers() returns a tuple of member (name, value).

    Returns:
        list: A sequence of database alias strings.

    """
    return [member[1] for member
        in inspect.getmembers(sys.modules[__name__])
        if member[0].startswith('ALIAS_')]

def get_ts_field_test_model_class_name(**kwargs):
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
    return TS_FIELD_TEST_PREFIX + suffix


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
