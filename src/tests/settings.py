"""
Django settings file only for use in testing.

See:
    https://docs.djangoproject.com/en/dev/topics/testing/advanced/#using-the-django-test-runner-to-test-reusable-applications

"""
SECRET_KEY = 'fake-key'

DATABASES = {
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'HOST': '127.0.0.1',
        'PASSWORD': 'tester',
        'PORT': '3306',
        'USER': 'tester',
    },
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
