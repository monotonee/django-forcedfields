"""
This file defines a set of very simple models for testing custom fields.

No static timestamp field is defined here due to the large number of different
keyword argument combinations that need to be tested. The test moodel classes
for the timestamp field are defined dynamically in this module.

"""

import sys

import django.db

import django_forcedfields
from . import utils as test_utils


class FixedCharRecord(django.db.models.Model):
    """
    Contains an instance of the fixed char field.

    """

    char_field_1 = django_forcedfields.FixedCharField(max_length=4)


# Dynamically generate timestamp field test models.
#
# A model is generated for each valid combination of field kwargs.
#
# Due to the need to test the table structure and field value output into the
# database, I needed a model instance for each possible timestamp field
# configuration. My options were:
#     1. Statically define models in the tests models module
#     2. Use type() to dynamically generate model classes directly in test cases
#     3. Dynamically define model classes here in the models module
#
# Option one seemed far too verbose, brittle, and tedious.
#
# Option two was attempted but a problem was encountered. When using Django's
# django.test.TestCase class, each test method is wrapped in a transaction.
# After defining a custom model class with type(), one needs to actually migrate
# it into one or more databases to test table structure and value insertion. DDL
# statements such as CREATE TABLE implicitly commit transactions in
# MySQL/MariaDB. I overrode
# django.db.backends.base.BaseDatabaseSchemaEditor.sql_create_table
# to create a TEMPORARY table instead and, altough this successfully created
# temp tables that could be used, there is no way to verify the correct table
# structure as temp tables are not visible in the information_schema. I could
# parse a SHOW CREATE TABLE <table_name> as it does acknowledge temp tables but
# that just seemed too smelly, brittle, and desperate. Another option was to use
# django.test.TransactionTestCase to avoid transactions altogether but, based on
# my experience, this greatly slows down tests although I'm still considering
# it. Note that PostgreSQL supports transactional DDL statements but
# unfortunately I can't just test PostgreSQL.
#
# Option three, while less appealing to me due to the vast number of models
# cluttering up the models module and making test DB setup and teardown slower,
# seems to work with Django's test infrastructure rather than against it. I'll
# use it for now.
#
# See:
# https://github.com/django/django/blob/master/django/db/backends/base/schema.py
# https://docs.python.org/3/library/functions.html#type
_THIS_MODULE = sys.modules[__name__]
for config in test_utils.TS_FIELD_TEST_CONFIGS:
    test_model_class_name = test_utils.get_ts_model_class_name(
        **config.kwargs_dict)
    test_model_class_members = {
        test_utils.TS_FIELD_TEST_ATTRNAME: django_forcedfields.TimestampField(
            **config.kwargs_dict),
        test_utils.UPDATE_FIELD_TEST_ATTRNAME: \
            django.db.models.SmallIntegerField(null=True),
        '__module__': __name__}
    test_model_class = type(
        test_model_class_name,
        (django.db.models.Model,),
        test_model_class_members)
    setattr(_THIS_MODULE, test_model_class_name, test_model_class)
