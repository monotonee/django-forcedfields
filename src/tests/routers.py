"""
See:
    https://docs.djangoproject.com/en/dev/topics/db/multi-db/#topics-db-multi-db-routing

"""

import django.db


class Router:
    """
    Ensures that the tests don't attempt to use the "default" DATABASE label.

    """

    DEFAULT_DATABASE = 'mysql'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._app_label = __name__.split('.')[0]

    def _get_database_key(self, model):
        """
        Determine the database config key for router suggestions.

        Args:
            model (django.db.models.Model)

        Returns:
            string: The DATABASES config key to use.

        """
        database_key = None
        if model._meta.app_label == self._app_label:
            database_key = self.DEFAULT_DATABASE
        return database_key

    def db_for_read(self, model, **hints):
        return self._get_database_key(model)

    def db_for_write(self, model, **hints):
        return self._get_database_key(model)

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Ensure the "default" DATABASES key is not used.

        """
        migration_allowed = True
        if app_label == self._app_label and db == django.db.DEFAULT_DB_ALIAS:
            migration_allowed = False
        return migration_allowed
