"""
Run tests by directly invoking this file from the Python interpreter.

Running tests after setting up a skeleton Django environment allows for the
use of Django testing tools. The default settings.TEST_RUNNER is currently
django.test.runner.DiscoverRunner.

See:
    https://docs.djangoproject.com/en/dev/topics/testing/advanced/#using-the-django-test-runner-to-test-reusable-applications
    https://docs.djangoproject.com/en/dev/topics/testing/overview/#running-tests
    https://github.com/django/django/blob/master/django/test/runner.py

"""

import argparse
import os
import sys

import django
from django.conf import settings
from django.test.utils import get_runner


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'test_labels',
        nargs='*',
        default=['tests'],
        help=(
            'Specific test label(s) to run. Test labels may be a full Python '
            'dotted path to a package, module, TestCase subclass, or test '
            'method.'))
    arguments = parser.parse_args()

    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=2)
    failures = test_runner.run_tests(arguments.test_labels)
    sys.exit(bool(failures))
