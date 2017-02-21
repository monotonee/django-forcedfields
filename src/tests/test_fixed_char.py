"""
This file contains tests of the fixed char field.

I'm not even going to attempt to mock and/or patch my way through Django's ORM.
I have opted to use small database service containers against which to run the
tests for a handful of database backends.

"""

from django.db import connections
import django.test

from . import models as test_models
import django_forcedfields


class TestFixedCharField(django.test.TestCase):
    """
    Defines tests for the fixed char field class.

    Since multiple database configs are defined in the settings.py and are being
    simultaneously tested, a series of class constants are defined here, each
    containing the value of its respective DATABASES alias. This makes it more
    explicit and readable which test is using what database and when.

    Originally, I attempted to leave the "default" DATABASES alias empty and to
    define each database by a non-default, explicit alias. However, despite my
    use of database routers, the Django TestCase still produced an error when
    tearing down the test case when the "default" alias was empty. The Django
    bug report below describes the error. For now, I'm just going to set
    "default" to point to the MySQL service instance as I'm tired of fighting
    with Django over anything remotely unusual in the way I want to structure
    my code.

    If memory serves, the Django test classes attempt to use the DATABASES
    alias' NAME parameter for the test database name suffix. Since there are no
    NAME parameters in the tests.settings module, the suffix is empty, resulting
    in "test_".

    See:
        https://code.djangoproject.com/ticket/25504
        https://docs.djangoproject.com/en/dev/topics/db/multi-db/
        https://github.com/django/django/blob/master/django/core/management/commands/inspectdb.py

    """
    _DB_MYSQL = 'default'
    _DB_POSTGRESQL = 'postgresql'
    _DB_SQLITE = 'sqlite3'

    multi_db = True
    _test_database_name = 'test_'

    @classmethod
    def setUpTestData(cls):
        cls._test_table_name = '_'.join([
            __name__.split('.')[0],
            test_models.FixedCharRecord.__name__.lower()])
        cls._test_field_name = test_models.FixedCharRecord._meta.fields[1]\
            .get_attname()
        cls._test_field_max_length = test_models.FixedCharRecord._meta\
            .fields[1].max_length

    def test_mysql_table_structure(self):
        """
        Test the creation of fixed char field in MySQL/MariaDB.

        I attempted to use Django's database introspection classes but Django
        wraps all the resulting data in arbitrary classes and named tuples while
        omitting the raw field data type that I actually want. I finally opted
        to use raw SQL.

        Example:
            connection = connections[alias]
            table_description = connection.introspection.get_table_description(
                connection.cursor(),
                test_table_name)

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/introspection.py
            https://github.com/django/django/blob/master/django/db/backends/mysql/introspection.py

        """
        sql_string = """
            SELECT
                DATA_TYPE
                ,CHARACTER_MAXIMUM_LENGTH
            FROM
                `information_schema`.`COLUMNS`
            WHERE
                `TABLE_SCHEMA` = %s
                AND `TABLE_NAME` = %s
                AND `COLUMN_NAME` = %s
        """
        sql_params = [
            self._test_database_name,
            self._test_table_name,
            self._test_field_name]

        cursor = connections[self._DB_MYSQL].cursor()
        cursor.execute(sql_string, sql_params)
        record = cursor.fetchone()

        self.assertEqual(record[0], 'char')
        self.assertEqual(record[1], self._test_field_max_length)

