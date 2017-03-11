"""
Note that include_package_data enables MANIFEST.in consumption.

See:
    https://setuptools.readthedocs.io/en/latest/setuptools.html#including-data-files

Using semantic verisioning.

See:
    https://www.python.org/dev/peps/pep-0440/#public-version-identifiers
    http://semver.org/

"""

import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    name='django-forcedfields',
    version='0.1.1',

    author='monotonee',
    author_email='monotonee@tuta.io',
    include_package_data=True,
    install_requires=[
        'django'
    ],
    license='MIT',
    packages=find_packages(exclude=('tests',)),
    py_modules=['django_forcedfields'],
    url='https://github.com/monotonee/django-forcedfields',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Database'
    ],
    description=(
        'Django model fields designed to more precisely define data types in '
        'database fields.'),
    keywords='char database django field model timestamp',
    long_description=README
)
