"""
This file defines a set of very simple models for testing custom fields.

"""

import django.db

import django_forcedfields


class FixedCharRecord(django.db.models.Model):
    """
    Contains an instance of the fixed char field.

    """

    char_field_1 = django_forcedfields.FixedCharField(max_length=4)






