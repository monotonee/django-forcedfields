"""
Django settings file only for use in testing.

See:
    https://docs.djangoproject.com/en/dev/topics/testing/advanced/#using-the-django-test-runner-to-test-reusable-applications

Originally, I attempted to leave the "default" DATABASES key empty and to define each database by a
non-default, explicit config label. However, despite my use of database routers, the Django
TestCase still produced an error when tearing down the test case when the "default" config was
empty. The Django bug report below describes the error. For now, I'm just going to set "default" to
point to the MySQL instance as I'm tired of fighting with Django over anything remotely unusual.

See:
    https://code.djangoproject.com/ticket/25504
    https://docs.djangoproject.com/en/dev/topics/db/multi-db/

"""

SECRET_KEY = 'fake-key'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'PASSWORD': 'tester',
        'PORT': '3306',
        'USER': 'tester',
    },
    # 'mariadb': {
        # 'ENGINE': 'django.db.backends.mysql',
        # 'HOST': '127.0.0.1',
        # 'PASSWORD': 'tester',
        # 'PORT': '3307',
        # 'USER': 'tester',
    # },
    'postgresql': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': '127.0.0.1',
        'PASSWORD': 'tester',
        'PORT': '5432',
        'USER': 'tester',
    },
    'sqlite3': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/django-forcedfields.sqlite3.db',
    }
}

INSTALLED_APPS = [
    'tests'
]

# Silence checks system warning:
#
# "HINT: It seems you set a fixed date / time / datetime value as default for this field." This may
# not be what you want. If you want to have the current date as default, use
# `django.utils.timezone.now`.
#
# Django seems to want one to pass a callable as the value of the field's "default" option. It needs
# to shut up. I know exactly what I'm doing and what I want. I need a fixed date in order to
# complete certain tests in the test suite.
#
# See:
#     https://github.com/django/django/blob/master/django/db/models/fields/__init__.py
#         django.db.models.fields.DateTimeCheckMixin.check()
#         django.db.models.fields.DateField._check_fix_default_value()
SILENCED_SYSTEM_CHECKS = ['fields.W161']

USE_TZ = False
TIME_ZONE = 'UTC'
