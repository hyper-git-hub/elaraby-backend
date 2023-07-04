from django.apps import AppConfig


class HypernetConfig(AppConfig):
    name = 'hypernet'

    def ready(self):
        # print("at ready")
        import hypernet.signals
