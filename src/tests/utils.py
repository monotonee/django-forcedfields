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


class FieldTestConfig:
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

    def __init__(self, *, kwargs_dict, db_type_dict, insert_values_dict):
        """
        Args:
            kwargs_dict (dict): A dictionary of the k/v pairs to be passed as keyword arguments to
                the custom field constructor.
            db_type_dict (dict): A dictionary of expected db_type output, keyed by connection alias.
            insert_values_dict (dict): A dictionary of test input values (keys) and the resulting
                values that are expected to be retrieved from the database (values) after new record
                insert.

        See:
            https://www.python.org/dev/peps/pep-3102/

        """
        self.kwargs_dict = kwargs_dict
        self.db_type_dict = db_type_dict
        self.insert_values_dict = insert_values_dict


class FieldTestConfigUtilityMixin:
    """
    A class desined to provide FieldTestConfig utility methods to test case classes.

    The provided methods facilitate interaction between a Django/unittest test case instance and a
    FieldTestConfig class.

    These methods are defined in a mixin class so they can easily access Django's TestCase assertion
    methods.

    """

    def _test_insert_dict(self, db_alias, model_class, model_attr, insert_value, expected_value):
        """
        Test INSERT and SELECT field attribute values from a FieldTestConfig.

        Inserts the test values for the given model, selects the value from the database, and
        compares the result with the expected value. Interprets the FieldTestCase.insert_values_dict
        and runs assertions based on the type and value of the data retrieved from the database
        after a successful insert.

        Args:
            db_alias (str): The string key under which a database configuration is defined. Usable in
                django.conf.settings or directly through django.db.connections.
            model_class (class): The class of the model that will issue the insert.
            model_attr (str): The model attribute through which the test field may be accessed.
            insert_value: The value to save in the new model instance's attribute.
            expected_value: The value that is expected to be retrieved from the database after a
                successful save() call.

        """
        if insert_value is django.db.models.NOT_PROVIDED:
            model = model_class()
        else:
            model_kwargs = {model_attr: insert_value}
            model = model_class(**model_kwargs)

        class_expected = inspect.isclass(expected_value)
        if class_expected and issubclass(expected_value, Exception):
            self.assertRaises(expected_value, model.save, using=db_alias)
        else:
            model.save(using=db_alias)
            retrieved_record_model = model_class.objects.using(db_alias).get(id=model.id)
            retrieved_value = getattr(retrieved_record_model, model_attr)
            if class_expected:
                retrieved_value = retrieved_value.__class__

            self.assertEqual(retrieved_value, expected_value)


def create_dict_string(source_dict):
    """
    Create a string from a dictionary.

    Generates a comma-delimited string of the dictionary's keys and values. Used for TestCase
    subtests to output the Field kwargs used during the subtest iteration.

    Example:
        create_dict_string({'first': 0, 'second': 1})
        >>> 'first=0, second=1'

    Args:
        source_dict (dict): The source dictionary.

    Returns:
        str: A comma-separated, string representation of the passed dictionary.

    """
    string_format = '{key!s}={value!s}'
    dict_string = ', '.join([
        string_format.format(key=key, value=value)
        for key, value
        in source_dict.items()
    ])

    return dict_string


def get_model_class_name(prefix, **kwargs):
    """
    Create a string for use as a dynamic class name.

    When testing all permutations of field keyword arguments in model classes, this function is used
    with the built-in function type() to dynamically generate the new model class' unique name.
    Subsequently, this function is called by the test suites to deterministically return a specific
    model class name based on desired field class configuration (kwargs). See sample usage of this
    function in the tests.models module.

    This algorithm is somewhat brittle. Not sure I like it.

    Args:
        prefix (str): The class name prefix.
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
    return prefix + suffix


def get_fc_model_class_name(**kwargs):
    """
    Generate the model class name for use in FixedCharField tests.

    Returns:
        str: The model class name.

    """
    return get_model_class_name(FC_MODEL_CLASS_NAME_PREFIX, **kwargs)


def get_ts_model_class_name(**kwargs):
    """
    Generate the model class name for use in TimestampField tests.

    Returns:
        str: The model class name.

    """
    return get_model_class_name(TS_MODEL_CLASS_NAME_PREFIX, **kwargs)


#######################
# Test Configurations #
#######################
# Django ORM doesn't permit value omission for fields in insert/update and so attempts to insert
# NULL when no value is provided for field on model (django.db.models.NOT_PROVIDED). This affects
# expected results of insert operations, most commonly by failing to emit IntegrityError and
# returning a None value instead.

# Configurations for FixedCharField tests.
# Note that empty string insert values are not tested. PostgreSQL returns an empty string of
# max_length while MySQL and SQLite return an empty string.
FC_DEFAULT_VALUE = 'four'
FC_DEFAULT_MAX_LENGTH = 4
FC_FIELD_ATTRNAME = 'fc_field_1'
FC_TEST_CONFIGS = [
    FieldTestConfig(
        kwargs_dict={'max_length': FC_DEFAULT_MAX_LENGTH},
        db_type_dict={
            ALIAS_MYSQL: 'CHAR(4)',
            ALIAS_POSTGRESQL: 'CHAR(4)',
            ALIAS_SQLITE: 'CHAR(4)'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: django.db.utils.IntegrityError,
            FC_DEFAULT_VALUE: FC_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'max_length': FC_DEFAULT_MAX_LENGTH, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'CHAR(4)',
            ALIAS_POSTGRESQL: 'CHAR(4)',
            ALIAS_SQLITE: 'CHAR(4)'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            FC_DEFAULT_VALUE: FC_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'default': FC_DEFAULT_VALUE, 'max_length': FC_DEFAULT_MAX_LENGTH},
        db_type_dict={
            ALIAS_MYSQL: 'CHAR(4) DEFAULT \'{!s}\''.format(FC_DEFAULT_VALUE),
            ALIAS_POSTGRESQL: 'CHAR(4) DEFAULT \'{!s}\''.format(FC_DEFAULT_VALUE),
            ALIAS_SQLITE: 'CHAR(4) DEFAULT \'{!s}\''.format(FC_DEFAULT_VALUE)
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: FC_DEFAULT_VALUE,
            None: django.db.utils.IntegrityError,
            FC_DEFAULT_VALUE: FC_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'default': FC_DEFAULT_VALUE, 'max_length': FC_DEFAULT_MAX_LENGTH, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'CHAR(4) DEFAULT \'{!s}\''.format(FC_DEFAULT_VALUE),
            ALIAS_POSTGRESQL: 'CHAR(4) DEFAULT \'{!s}\''.format(FC_DEFAULT_VALUE),
            ALIAS_SQLITE: 'CHAR(4) DEFAULT \'{!s}\''.format(FC_DEFAULT_VALUE)
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: FC_DEFAULT_VALUE,
            None: None,
            FC_DEFAULT_VALUE: FC_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'default': None, 'max_length': FC_DEFAULT_MAX_LENGTH, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'CHAR(4) DEFAULT NULL',
            ALIAS_POSTGRESQL: 'CHAR(4) DEFAULT NULL',
            ALIAS_SQLITE: 'CHAR(4) DEFAULT NULL'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            FC_DEFAULT_VALUE: FC_DEFAULT_VALUE
        }
    )
]
FC_MODEL_CLASS_NAME_PREFIX = 'FCRecord'


# Configurations for TimestampField tests.
TS_DEFAULT_VALUE = datetime.datetime.now().replace(microsecond=0)
TS_DEFAULT_VALUE_STR = str(TS_DEFAULT_VALUE)
TS_FIELD_ATTRNAME = 'ts_field_1'
TS_TEST_CONFIGS = [
    FieldTestConfig(
        kwargs_dict={},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE',
            ALIAS_SQLITE: 'DATETIME'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: django.db.utils.IntegrityError,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE',
            ALIAS_SQLITE: 'DATETIME'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
            ALIAS_SQLITE: 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            TS_DEFAULT_VALUE: datetime.datetime
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now': True, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
            ALIAS_SQLITE: 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            TS_DEFAULT_VALUE: datetime.datetime
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_add': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
            ALIAS_SQLITE: 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            TS_DEFAULT_VALUE: datetime.datetime
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_add': True, 'auto_now_update': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
            ALIAS_SQLITE: 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            TS_DEFAULT_VALUE: datetime.datetime
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_add': True, 'auto_now_update': True, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
            ALIAS_SQLITE: 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            TS_DEFAULT_VALUE: datetime.datetime
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_add': True, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP',
            ALIAS_SQLITE: 'DATETIME DEFAULT CURRENT_TIMESTAMP'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: datetime.datetime,
            None: datetime.datetime,
            TS_DEFAULT_VALUE: datetime.datetime
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_update': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE',
            ALIAS_SQLITE: 'DATETIME'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: django.db.utils.IntegrityError,
            None: django.db.utils.IntegrityError,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_update': True, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE',
            ALIAS_SQLITE: 'DATETIME'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_update': True, 'default': TS_DEFAULT_VALUE},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT \'{!s}\' ON UPDATE CURRENT_TIMESTAMP'.format(
                TS_DEFAULT_VALUE_STR
            ),
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'{!s}\''.format(
                TS_DEFAULT_VALUE_STR
            ),
            ALIAS_SQLITE: 'DATETIME DEFAULT \'{!s}\''.format(TS_DEFAULT_VALUE_STR)
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: TS_DEFAULT_VALUE,
            None: django.db.utils.IntegrityError,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'auto_now_update': True, 'default': TS_DEFAULT_VALUE, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT \'{!s}\' ON UPDATE CURRENT_TIMESTAMP'.format(
                TS_DEFAULT_VALUE_STR
            ),
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'{!s}\''.format(
                TS_DEFAULT_VALUE_STR
            ),
            ALIAS_SQLITE: 'DATETIME DEFAULT \'{!s}\''.format(TS_DEFAULT_VALUE_STR)
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: TS_DEFAULT_VALUE,
            None: None,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'default': TS_DEFAULT_VALUE},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT \'{!s}\''.format(TS_DEFAULT_VALUE_STR),
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'{!s}\''.format(
                TS_DEFAULT_VALUE_STR
            ),
            ALIAS_SQLITE: 'DATETIME DEFAULT \'{!s}\''.format(TS_DEFAULT_VALUE_STR)
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: TS_DEFAULT_VALUE,
            None: django.db.utils.IntegrityError,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'default': TS_DEFAULT_VALUE, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT \'{!s}\''.format(TS_DEFAULT_VALUE_STR),
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT \'{!s}\''.format(
                TS_DEFAULT_VALUE_STR
            ),
            ALIAS_SQLITE: 'DATETIME DEFAULT \'{!s}\''.format(TS_DEFAULT_VALUE_STR)
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: TS_DEFAULT_VALUE,
            None: None,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    ),
    FieldTestConfig(
        kwargs_dict={'default': None, 'null': True},
        db_type_dict={
            ALIAS_MYSQL: 'TIMESTAMP DEFAULT NULL',
            ALIAS_POSTGRESQL: 'TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL',
            ALIAS_SQLITE: 'DATETIME DEFAULT NULL'
        },
        insert_values_dict={
            django.db.models.NOT_PROVIDED: None,
            None: None,
            TS_DEFAULT_VALUE: TS_DEFAULT_VALUE
        }
    )
]
TS_MODEL_CLASS_NAME_PREFIX = 'TsRecord'
TS_UPDATE_FIELD_ATTRNAME = 'update_field_1'
