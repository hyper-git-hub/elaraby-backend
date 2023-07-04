__author__ = 'nahmed'


class HypernetProxyDBRouter(object):
    """
        DB router to use 'hypernet-proxy' Database (instead of 'default') for proxy related tables.
    """

    def db_for_read(self, model, **hints):
        """
        Send all read operations on proxy_* app models to `hypernet-proxy`.
        """
        if model._meta.app_label == 'data_handler':
            return 'hypernet-proxy'
        return None

    def db_for_write(self, model, **hints):
        """
        Send all write operations on Example app models to `example_db`.
        """
        if model._meta.app_label == 'data_handler':
            return 'hypernet-proxy'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Determine if relationship is allowed between two objects.
        """

        # Allow any relation between two models that are both in the Example app.
        if obj1._meta.app_label == 'data_handler' and obj2._meta.app_label == 'data_handler':
            return True
        # No opinion if neither object is in the Example app (defer to default or other routers).
        elif 'data_handler' not in [obj1._meta.app_label, obj2._meta.app_label]:
            return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
            Ensure that the Example app's models get created on the right database.
        """
        if app_label == 'data_handler':
            # The Example app should be migrated only on the example_db database.
            return db == 'hypernet-proxy'
        elif db == 'hypernet-proxy':
            # Ensure that all other apps don't get migrated on the example_db database.
            return False
        # No opinion for all other scenarios
        return None