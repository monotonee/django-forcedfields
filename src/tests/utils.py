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


ALIAS_MYSQL = 'default'
ALIAS_POSTGRESQL = 'postgresql'
ALIAS_SQLITE = 'sqlite3'

TEST_DB_NAME = 'test_'


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

def get_test_table_name(model):
    """
    Return the name of the test DB table.

    Args:
        model (django.db.models): A model instance from which Django's TestCase
            generates a test table.

    Returns:
        string: The name of the generated test table.

    """
    return '_'.join([__name__.split('.')[0], model.__name__.lower()])
