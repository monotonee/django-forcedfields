###################
django-forcedfields
###################

.. image:: https://img.shields.io/pypi/v/django-forcedfields.svg
   :target: https://pypi.python.org/pypi/django-forcedfields

*******
Summary
*******

A Python module that provides a set of custom, specialized Django model fields.

While I haved worked with Django's ORM for some time and have enjoyed many of
its features for simple use cases, I find myself increasingly impeded, annoyed,
and dissatisfied by its limitations in complex applications. One glaring problem
in my eyes is the ORM's lack of semantic database field data types and
modifiers.

For example, an eight-character varchar field that can be null and that has a
default value of 'elegy' will not result in the MySQL
`DDL <https://dev.mysql.com/doc/refman/en/glossary.html#glos_ddl>`_::

    VARCHAR(8) DEFAULT 'elegy' NULL

but simply as::

    VARCHAR(8) NULL

While this varchar example may not be the most egregious, it nonetheless
illustrates a complete reliance upon the application and its ORM for behavior
that should be handled, and indeed is best handled, by the database management
system itself.

Databases should be as self-documenting and semantic as possible, independent of
any application code, ORM models, or documentation. I will not compromise this
principle for the sake of an ORM's conveniences. To this end, I have begun to
create these custom Django model fields to force Django to issue the most
specific and complete DDL statements possible. It is my goal with these and
future fields to shift responsibility from the application ORM to the underlying
database wherever possible while maintaining a consistent and complete ORM
interface and database backend abstraction.

************
Installation
************
::

    pip install [--user] django-forcedfields

*************
Example Usage
*************
::

    import django_forcedfields as forcedfields

or::

    from django_forcedfields import TimestampField

******
Fields
******

FixedCharField
==============

**class FixedCharField(max_length=None, **options)**

This field extends Django's `CharField
<https://docs.djangoproject.com/en/dev/ref/models/fields/#charfield>`_.

This field inherits all functionality and interfaces from Django's standard
CharField but, rather than producing a ``VARCHAR`` field in the database, the
FixedCharField creates a ``CHAR`` field. The parent CharField class' keyword
argument "max_length" is retained and, when passed, specifies the ``CHAR``
field's max length just like it does for the ``VARCHAR`` implementation.

The ``CHAR`` field is supported on all RDBMS in common use with Django.

The current implementation of the FixedCharField does not output complete DDL.
Future development will add the ``DEFAULT`` modifier clause when necessary.

A note here on Django's `admonition on null values with text fields
<https://docs.djangoproject.com/en/dev/ref/models/fields/#null>`_: Django is
wrong. ``NULL`` means unknown data, an empty string means an empty string. Their
meanings are semantically different by definition. Set ``null=True`` on text
fields when your use case warrants it. That is, when you may have a complete
absence of data as well as the need to record an empty string. Google this topic
for more analysis.

TimestampField
==============

**class TimestampField(auto_now=False, auto_now_add=False,
auto_now_update=False, **options)**

This field extends Django's `DateTimeField
<https://docs.djangoproject.com/en/dev/ref/models/fields/#datetimefield>`_.

This field supports all `DateTimeField keyword arguments
<https://docs.djangoproject.com/en/dev/ref/models/fields/#datefield>`_ and
adds a new "auto_now_update" argument.

**TimestampField.auto_now_update**
    auto_now_update is a boolean that, when True, sets a new timestamp field
    value on update operations *only*, not on insert.

    This option is mutually exclusive with auto_now.

Like its parent DateTimeField, the TimestampField's options auto_now,
auto_now_add, and auto_now_update will forcibly overwrite any manually-set model
field attribute values when enabled and when their conditions are triggered.

A timestamp is well-suited to record system and database record metadata such as
record insert and update times. Due to the database data type features, it is
also ideal when storing a fixed point in time, independent of time zone.
Although the creation of the TimestampField was largely motivated by the need
for an ORM abstraction for metadata fields, it can also be used just like its
parent DateTimeField as long as one understands the data type's different
advantages and limitations.

Instead of DateTimeField's reliance on ``DATETIME`` and similar data types, the
TimestampField uses ``TIMESTAMP`` data type and other data types that do not
store time zone information. The data type changes can be seen in the following
table:

========== ======================= ===========================
database   DateTimeField data type TimestampField data type
========== ======================= ===========================
MySQL      DATETIME                TIMESTAMP
PostgreSQL TIMESTAMP WITH TIMEZONE TIMESTAMP WITHOUT TIME ZONE
sqlite     DATETIME                DATETIME
========== ======================= ===========================

Also note that standard DDL modifiers such as ``DEFAULT CURRENT TIMESTAMP`` and
non-standard ones such as MySQL's ``ON UPDATE CURRENT_TIMESTAMP`` are used when
the corresponding options are enabled.

Naturally, when designing a system field instead of a user data field, the need
to offload responsibility to the underlying database becomes greater. If the
data is for system and metadata purposes, then it increases consistency and
data integrity to delegate field value management to the system itself.
Unfortunately, Django's ORM made this difficult.

In implementing Django custom field method overrides, I attempted to use
database backend-specific functions and keywords such as ``NOW()`` and
``CURRENT_TIMESTAMP`` to allow the database management system to set its own
timestamp rather than generating the value from the application layer. However,
in methods such as `get_db_prep_value
<https://docs.djangoproject.com/en/dev/ref/models/fields/#django.db.models.Field.get_prep_value>`_,
the return value is always quoted in the final, compiled SQL, causing some
databases to emit errors. I finally conceded (temporary) defeat and reverted to
application-generated timestamp values.

******************************
Database Engine Considerations
******************************

When using TimestampField, one must be aware of certain database engine behavior defaults and
configurations. An ORM is usually designed to abstract, as much as is practical and prudent, the
differences between the underlying databases. In this case, however, the abstraction leaks. Consider
the following timestamp column DDL::

    TIMESTAMP NOT NULL

Note the lack of a ``DEFAULT`` clause. One would expect, upon attempting to insert a ``NULL`` value
or failing to provide a value for the columns altogether, that some sort of constraint or integrity
exception would be raised. Indeed, this behavior adheres to the principle of least astonishment and
is the standard behavior of both SQLite and PostgreSQL. Both `SQLite
<https://www.sqlite.org/lang_createtable.html>`_ and `PostgreSQL
<https://www.postgresql.org/docs/current/static/ddl-default.html>`_ implicitly assign
``DEFAULT NULL`` to column definitions with no explicit ``DEFAULT`` clause.

MySQL requires a specific configuration to achieve the same standard behavior. The following
configuration options affect ``TIMESTAMP`` columns:

- `strict mode <https://dev.mysql.com/doc/refman/en/sql-mode.html#sql-mode-strict>`_
- `NO_ZERO_DATE <https://dev.mysql.com/doc/refman/en/sql-mode.html#sqlmode_no_zero_date>`_
- `NO_ZERO_IN_DATE <https://dev.mysql.com/doc/refman/en/sql-mode.html#sqlmode_no_zero_in_date>`_
- `explicit_defaults_for_timestamp <https://dev.mysql.com/doc/refman/en/server-system-variables.html#sysvar_explicit_defaults_for_timestamp>`_

At minimum, MySQL requires that both strict mode and ``explicit_defaults_for_timestamp`` are
enabled for ``TIMESTAMP`` behavior to conform to standards. If one attempts to omit a value for the
``TIMESTAMP NOT NULL`` column, a "ERROR 1364 (HY000): Field <field_name> doesn't have a default
value" is emitted and if one attempts to insert a ``NULL`` value, a "ERROR 1048 (23000): Column
<field_name> cannot be null" is emitted. As of version MySQL 5.7, strict mode is enabled by default
but ``explicit_defaults_for_timestamp`` is not.

MariaDB, on the other hand, applies the same configuration parameters in a different way and its
logic as it relates to ``TIMESTAMP NOT NULL`` is less clear and, dare I say, erroneous. Assuming
identical configuration (strict mode and ``explicit_defaults_for_timestamp`` enabled), MariaDB
raises "ERROR 1364 (HY000): Field <field_name> doesn't have a default value" on insert value
omission but successfully accepts a ``NULL`` value with no error and stores the results of
``CURRENT_TIMESTAMP()`` in the field instead.

In an attempt to bring MariaDB in line with the standard, I also tested ``NO_ZERO_DATE`` and
``NO_ZERO_IN_DATE``. As long as both ``explicit_defaults_for_timestamp`` and ``NO_ZERO_DATE`` or
``NO_ZERO_IN_DATE`` are enabled, it is impossible to create a table containing the
``TIMESTAMP NOT NULL`` column as the ``CREATE TABLE`` statement fails with "ERROR 1067 (42000):
Invalid default value for <field_name>". This suggests that not only is the ``DEFAULT`` value
validated during DDL statements, but MariaDB is also attempting to implicitly insert a zero value
timestamp into the ``TIMESTAMP`` field. Taken from the `MySQL documentation
<https://dev.mysql.com/doc/refman/en/datetime.html>`_:

    Invalid DATE, DATETIME, or TIMESTAMP values are converted to the “zero” value of the appropriate
    type ('0000-00-00' or '0000-00-00 00:00:00').

In conclusion, it is impossible for MariaDB's ``TIMESTAMP`` fields to behave in a standard way when
dealing with ``TIMESTAMP NOT NULL`` columns. I found `this bug report
<https://jira.mariadb.org/browse/MDEV-10802>`_ for MariaDB but it appears that the work has ceased
and the fix has not been merged into the target release. All tests were performed on MariaDB 10.2
and 10.3.

I now have a choice to make: do I cause TimestampField to step aside and let the user more directly
experience the effects of the underlying database engine's configuration or do I attempt to abstract
the behavior differences as much as possible? Given the spirit and goal of this library, I have
opted for less abstraction and have removed any additional, artificial normalization of database
engine behavior in these field classes. I am certainly open to discussion on this point so please
don't hesitate to open communication with me or point out any errors in my testing.

Given MariaDB's deviation from standards, this package's unit tests are performed using MySQL and
testing on MariaDB is disabled until further notice.

As an aside, please note that many inconsistent behaviors between database engines can be mitigated
or even eliminated by explicitly defining field keyword arguments such as ``default``, ``null``,
etc., causing more explicit DDL SQL to be generated by Django in the resulting migrations and SQL.

***********
Development
***********

To set up the development environment, a Vagrantfile is included. Install
`Vagrant <https://www.vagrantup.com/>`_ and::

    vagrant up

Once Vagrant has completed provisioning, ``vagrant ssh`` into the box and start
the database servers against which to run the test suite::

    docker-compose up -d

Finally, run the tests with::

    make tests

In this project, I use `Google's Python style guide
<https://google.github.io/styleguide/pyguide.html>`_. Pylint doesn't play nicely
with some of the styles. A few notes on pylint:

* bad-continuation

    * Ignore most of these. Google style guide allows for a 4-space hanging
      indent with nothing on first line.
    * Example: `line length
      <https://google.github.io/styleguide/pyguide.html?showone=Line_length#Line_length>`_
    * Example: `indentation
      <https://google.github.io/styleguide/pyguide.html?showone=Indentation#Indentation>`_

* bad-super-call

    * Ignore this. I use the first argument of Python's build-in ``super()`` to
      define the method resolution order and pass ``self`` as the second
      argument to bind the method call to the current instance.
    * `super() <https://docs.python.org/3/library/functions.html#super>`_

**************
Oracle Support
**************

The FixedCharField should work on Oracle but the TimestampField will default to
DateTimeField database field data types when used with Oracle. I did not test
Oracle for a few reasons:

#. It is too difficult to get an Oracle server instance against which to test.
   As one can see, I use lightweight Docker containerized services to run the
   test databases. To use Oracle, one needs to provide the Oracle installation
   binaries. To get the binaries, one needs to sign in to Oracle's web site for
   the privilege of downloading over 2.5 gigabytes. Too much unnecessary pain,
   not enough return. If you use Oracle products, I sympathize and may god have
   mercy on your soul.

    * https://github.com/oracle/docker-images/tree/master/OracleDatabase

#. Oracle seems to be `rarely used with Django
   <https://www.djangosites.org/stats/>`_.
#. I hate Oracle products and Oracle as an entity.
