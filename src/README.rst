###################
django-forcedfields
###################

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

Development
===========

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

Oracle Support
==============

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
