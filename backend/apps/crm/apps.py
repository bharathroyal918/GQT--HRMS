"""CRM application configuration."""
from django.apps import AppConfig


class CrmConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.crm"
    verbose_name = "Recruitment CRM & Company Acquisition"

