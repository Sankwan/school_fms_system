from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users & Authentication'

    def ready(self):
        """Register signal handlers for login/logout audit logging."""
        import apps.users.signals  # noqa: F401
