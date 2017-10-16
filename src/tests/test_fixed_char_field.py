"""
Tests of FixedCharField.

"""

import unittest.mock as mock

import django.conf
import django.core.exceptions
import django.db
import django.test

import django_forcedfields as forcedfields
from . import models as test_models
from . import utils as test_utils


class TestFixedCharField(django.test.TestCase):
    """
    Defines tests for the fixed char field class.

    """

    multi_db = True

    @classmethod
    def setUpTestData(cls):
        """
        Override django.test.TestCase.setUpTestData().

        Not a member of TransactionTestCase.

        """
        cls._db_aliases = test_utils.get_db_aliases()

    def test_db_type(self):
        """
        Test simple output of the field's overridden "db_type" method.

        """
        for db_alias in self._db_aliases:
            db_connection = django.db.connections[db_alias]
            db_backend = db_connection.settings_dict['ENGINE']
            for test_config in test_utils.FC_TEST_CONFIGS:
                field_kwarg_format = '{key!s}={value!s}'
                field_kwarg_string = ', '.join([
                    field_kwarg_format.format(key=key, value=value)
                    for key, value
                    in test_config.kwargs_dict.items()
                ])
                with self.subTest(backend=db_backend, kwargs=field_kwarg_string):
                    field = forcedfields.FixedCharField(**test_config.kwargs_dict)
                    returned_db_type = field.db_type(db_connection)
                    expected_db_type = test_config.db_type_dict[db_alias]

                    self.assertEqual(returned_db_type, expected_db_type)

    def test_max_length_validation(self):
        """
        Test that max_length validation functions correctly.

        Probably not strictly necessary but I want to ensure that the custom field class method
        overrides don't affect standard operations.

        Note:
            Validation covers actual model attribute values, not the field class instance arguments.
            Checks cover the field class arguments and configuration.

        """
        test_model = test_models.FixedCharRecord(char_field_1='too many chars')
        self.assertRaises(django.core.exceptions.ValidationError, test_model.full_clean)

    def test_mysql_table_structure(self):
        """
        Test the creation of fixed char field in MySQL/MariaDB.

        Because all db_type method return values were tested in another test case, this method will
        only run a cursory set of checks on the actual database table structure. This module is
        supposed to test the custom field, not the underlying database.

        I attempted to use Django's database introspection classes but Django wraps all the
        resulting data in arbitrary classes and named tuples while omitting the raw field data type
        that I actually want. I finally opted to use raw SQL.

        Example:
            connection = connections[alias]
            table_description = connection.introspection.get_table_description(
                connection.cursor(),
                test_table_name
            )

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/introspection.py
            https://github.com/django/django/blob/master/django/db/backends/mysql/introspection.py

        In django.db.backends.base.creation.BaseDatabaseCreation.create_test_db, the DATABASES alias
        NAME parameter is overwritten by the results of the same object's _get_test_db_name()
        method. Therefore, we can get the generated name of the test DB from the connection's
        settings_dict.

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/creation.py

        """
        model_class_name = test_utils.get_fc_model_class_name(
            default=test_utils.FC_DEFAULT_VALUE,
            max_length=test_utils.FC_DEFAULT_MAX_LENGTH
        )
        model_class = getattr(test_models, model_class_name)
        connection = django.db.connections[test_utils.ALIAS_MYSQL]

        sql_string = """
            SELECT
                LOWER(`DATA_TYPE`) AS `DATA_TYPE`,
                LOWER(`IS_NULLABLE`) AS `IS_NULLABLE`,
                LOWER(CAST(`COLUMN_DEFAULT` AS CHAR(32))) AS `COLUMN_DEFAULT`,
                `CHARACTER_MAXIMUM_LENGTH`
            FROM
                `information_schema`.`COLUMNS`
            WHERE
                `TABLE_SCHEMA` = %s
                AND `TABLE_NAME` = %s
                AND `COLUMN_NAME` = %s
        """
        sql_params = [
            connection.settings_dict['NAME'],
            model_class._meta.db_table,
            model_class._meta.fields[1].get_attname_column()[1]
        ]

        with connection.cursor() as cursor:
            cursor.execute(sql_string, sql_params)
            record = cursor.fetchone()

        self.assertEqual(record[0], 'char')
        self.assertEqual(record[1], 'no')
        self.assertEqual(record[2], test_utils.FC_DEFAULT_VALUE)
        self.assertEqual(record[3], test_utils.FC_DEFAULT_MAX_LENGTH)

    def test_postgresql_table_structure(self):
        """
        Test the creation of fixed char field in PostgreSQL.

        Because all db_type method return values were tested in another test case, this method will
        only run a cursory set of checks on the actual database table structure. This module is
        supposed to test the custom field, not the underlying database.

        I attempted to use Django's database introspection classes but Django wraps all the
        resulting data in arbitrary classes and named tuples while omitting the raw field data type
        that I actually want. I finally opted to use raw SQL.

        Example:
            connection = connections[alias]
            table_description = connection.introspection.get_table_description(
                connection.cursor(),
                test_table_name)

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/introspection.py
            https://github.com/django/django/blob/master/django/db/backends/mysql/introspection.py

        In django.db.backends.base.creation.BaseDatabaseCreation.create_test_db, the DATABASES alias
        NAME parameter is overwritten by the results of the same object's _get_test_db_name()
        method. Therefore, we can get the generated name of the test DB from the connection's
        settings_dict.

        See:
            https://github.com/django/django/blob/master/django/db/backends/base/creation.py

        """
        model_class_name = test_utils.get_fc_model_class_name(
            default=test_utils.FC_DEFAULT_VALUE,
            max_length=test_utils.FC_DEFAULT_MAX_LENGTH
        )
        model_class = getattr(test_models, model_class_name)
        connection = django.db.connections[test_utils.ALIAS_POSTGRESQL]

        # See: https://www.postgresql.org/docs/current/static/typeconv-query.html
        expected_column_default = '\'{!s}\'::bpchar'.format(test_utils.FC_DEFAULT_VALUE)

        sql_string = """
            SELECT
                LOWER(data_type) AS data_type,
                LOWER(is_nullable) AS is_nullable,
                LOWER(column_default) AS column_default,
                character_maximum_length
            FROM
                information_schema.columns
            WHERE
                table_catalog = %s
                AND table_name = %s
                AND column_name = %s
        """
        sql_params = [
            connection.settings_dict['NAME'],
            model_class._meta.db_table,
            model_class._meta.fields[1].get_attname_column()[1]
        ]

        with connection.cursor() as cursor:
            cursor.execute(sql_string, sql_params)
            record = cursor.fetchone()

        self.assertEqual(record[0], 'character')
        self.assertEqual(record[1], 'no')
        self.assertEqual(record[2], expected_column_default)
        self.assertEqual(record[3], test_utils.FC_DEFAULT_MAX_LENGTH)

    def test_save(self):
        """
        Test that data is correctly saved through the field class.

        Probably not strictly necessary but I want to ensure that the custom field class method
        overrides don't affect standard operations.

        """
        expected_value = 'five'
        model_class_name = test_utils.get_fc_model_class_name(
            **test_utils.FC_TEST_CONFIGS[0].kwargs_dict
        )
        model_class = getattr(test_models, model_class_name)
        model_kwargs = {test_utils.FC_FIELD_ATTRNAME: expected_value}
        model = model_class(**model_kwargs)

        for db_alias in self._db_aliases:
            db_backend = django.conf.settings.DATABASES[db_alias]['ENGINE']
            with self.subTest(backend=db_backend):
                model.save(using=db_alias)
                result_record = model_class.objects.using(db_alias).get(**model_kwargs)

                self.assertEqual(
                    getattr(result_record, test_utils.FC_FIELD_ATTRNAME),
                    expected_value
                )

    def test_save_null(self):
        """
        Test that NULL or None is correctly saved when model field attribute is None.

        The Python database backend converts NULL values to None. The ORM appears to have no part
        in the value conversion. Therefore, a simple test for None is acceptable for now.

        As an aside, I did run a one-time test to ascertain for certain if NULL was stored in the
        database. After changing this TestCase to a TransactionTestCase to avoid per-test
        transactions, I logged in to the MySQL server through the MySQL CLI and verified that the
        ORM does insert a NULL value when passed an instance of Python's None.

        In addition, I verified in the source code that the ORM updates fields with NULL values for
        Python's None.

        See:
            https://github.com/django/django/blob/master/django/db/models/sql/compiler.py
                django.db.models.sql.compiler.SQLUpdateCompiler.as_sql

        This test is not strictly necessary but I want to ensure that the custom field class method
        overrides don't affect standard operations.

        """
        model_class_name = test_utils.get_fc_model_class_name(
            **test_utils.FC_TEST_CONFIGS[2].kwargs_dict
        )
        model_class = getattr(test_models, model_class_name)
        model_kwargs = {test_utils.FC_FIELD_ATTRNAME: None}
        model = model_class(**model_kwargs)

        for db_alias in self._db_aliases:
            db_backend = django.conf.settings.DATABASES[db_alias]['ENGINE']
            with self.subTest(backend=db_backend):
                model.save(using=db_alias)
                result_record = model_class.objects.using(db_alias).get(**model_kwargs)

                self.assertEqual(getattr(result_record, test_utils.FC_FIELD_ATTRNAME), None)

    def test_sqlite_table_structure(self):
        """
        Test correct DB table structures with sqlite3 backend.

        Because all db_type method return values were tested in another test case, this method will
        only run a cursory set of checks on the actual database table structure. This module is
        supposed to test the custom field, not the underlying database.

        Apparently PRAGMA statements cannot be prepared and/or parameterized. A sqlite syntax
        exception is raised if one attempts to pass parameters to cursor.execute().

        The PRAGMA table_info() return columns:
        >>> [desc[0] for desc in cursor.description]
        >>> ['cid', 'name', 'type', 'notnull', 'dflt_value', 'pk']

        See:
            https://www.sqlite.org/pragma.html#pragma_table_info
            https://docs.djangoproject.com/en/dev/topics/db/sql/#executing-custom-sql-directly

        """
        model_class_name = test_utils.get_fc_model_class_name(
            default=test_utils.FC_DEFAULT_VALUE,
            max_length=test_utils.FC_DEFAULT_MAX_LENGTH
        )
        model_class = getattr(test_models, model_class_name)
        connection = django.db.connections[test_utils.ALIAS_SQLITE]

        sql_string = 'PRAGMA table_info({!s})'.format(model_class._meta.db_table)

        with connection.cursor() as cursor:
            cursor.execute(sql_string)
            records = cursor.fetchall()
        record = records[1]

        self.assertEqual(record[2], 'CHAR({!s})'.format(test_utils.FC_DEFAULT_MAX_LENGTH)) # type
        self.assertEqual(record[3], 1) # notnull
        self.assertEqual(record[4], '\'{!s}\''.format(test_utils.FC_DEFAULT_VALUE)) # dflt_value
