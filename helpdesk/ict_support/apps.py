# ict_support/apps.py
from django.apps import AppConfig

class IctSupportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ict_support'
    verbose_name = "ICT Support" 

    def ready(self):
        import ict_support.signals  # ensures signals are registered
