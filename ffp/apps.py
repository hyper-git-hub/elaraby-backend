from django.apps import AppConfig


class FfpConfig(AppConfig):
    name = 'ffp'

    def ready(self):
        from .signals import violation_notifications_ffp
        