"""
Tests of the fixed char field using a real DB backend.

I'm not even going to attempt to mock and/or patch my way through Django's ORM.
I have opted to use small database service containers against which to run the
tests for a handful of database backends.

"""

import inspect
import unittest.mock as mock

import django.conf
import django.core.exceptions
import django.db
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
    _ALIAS_MYSQL = 'default'
    _ALIAS_POSTGRESQL = 'postgresql'
    _ALIAS_SQLITE = 'sqlite3'

    _test_database_name = 'test_'
    multi_db = True

    @classmethod
    def setUpTestData(cls):
        """
        TODO: Get test DB entity names from Django's TestCase class directly?

        """
        cls._test_table_name = '_'.join([
            __name__.split('.')[0],
            test_models.FixedCharRecord.__name__.lower()])
        cls._test_field_name = test_models.FixedCharRecord._meta.fields[1]\
            .get_attname()
        cls._test_field_max_length = test_models.FixedCharRecord._meta\
            .fields[1].max_length

        # inspect.getmembers() returns a tuple of member (name, value)
        cls._db_aliases = [member[1] for member
            in inspect.getmembers(cls)
            if member[0].startswith('_ALIAS')]

    def test_db_type(self):
        """
        Test simple output of the field's overridden "db_type" method.

        """
        test_field = django_forcedfields.FixedCharField(
            max_length=self._test_field_max_length)
        expected_return_value = 'char({!s})'.format(self._test_field_max_length)

        for alias in self._db_aliases:
            settings_dict = django.conf.settings.DATABASES[alias]
            connection_mock = mock.NonCallableMock(
                settings_dict=settings_dict)
            type_string = test_field.db_type(connection_mock)

            with self.subTest(backend=settings_dict['ENGINE']):
                self.assertEqual(type_string, expected_return_value)

    def test_max_length_validation(self):
        """
        Test that max_length is enforced.

        Probably not strictly necessary but I want to ensure that the custom
        field class method overrides don't affect standard operations.

        """
        test_model = test_models.FixedCharRecord(char_field_1='too many chars')
        self.assertRaises(
            django.core.exceptions.ValidationError,
            test_model.full_clean)

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
                `DATA_TYPE`
                ,`CHARACTER_MAXIMUM_LENGTH`
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

        cursor = django.db.connections[self._ALIAS_MYSQL].cursor()
        cursor.execute(sql_string, sql_params)
        record = cursor.fetchone()

        self.assertEqual(record[0], 'char')
        self.assertEqual(record[1], self._test_field_max_length)

    def test_postgresql_table_structure(self):
        """
        Test the creation of fixed char field in PostgreSQL.

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
                data_type
                ,character_maximum_length
            FROM
                information_schema.columns
            WHERE
                table_catalog = %s
                AND table_name = %s
                AND column_name = %s
        """
        sql_params = [
            self._test_database_name,
            self._test_table_name,
            self._test_field_name]

        cursor = django.db.connections[self._ALIAS_POSTGRESQL].cursor()
        cursor.execute(sql_string, sql_params)
        record = cursor.fetchone()

        self.assertEqual(record[0], 'character')
        self.assertEqual(record[1], self._test_field_max_length)

    def test_save(self):
        """
        Test that data is correctly saved through the field class.

        Probably not strictly necessary but I want to ensure that the custom
        field class method overrides don't affect standard operations.

        """
        test_value = 'four'
        test_model = test_models.FixedCharRecord(char_field_1=test_value)
        for alias in self._db_aliases:
            db_backend = django.conf.settings.DATABASES[alias]['ENGINE']

            with self.subTest(backend=db_backend):
                test_model.save(using=alias)
                result_record = test_models.FixedCharRecord.objects\
                    .using(alias).get(char_field_1=test_value)
                self.assertEqual(result_record.char_field_1, test_value)

