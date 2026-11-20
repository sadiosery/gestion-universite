from django.apps import AppConfig


class UniversiteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'universite'
    verbose_name = 'Gestion Universitaire'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in
        from .sauvegarde import sauvegarde_si_requise

        user_logged_in.connect(
            lambda sender, **kwargs: sauvegarde_si_requise(), weak=False)
