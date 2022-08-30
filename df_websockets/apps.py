from django.apps import AppConfig


class DfWebsocketsApp(AppConfig):
    name = "df_websockets"
    verbose_name = "Websockets for Django"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # noinspection PyUnresolvedReferences
        import df_websockets.checks
