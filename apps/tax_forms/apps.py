from django.apps import AppConfig


class TaxFormsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tax_forms'
    verbose_name = 'Tax Forms'

    def ready(self):
        from .signals import connect_signals
        connect_signals()
