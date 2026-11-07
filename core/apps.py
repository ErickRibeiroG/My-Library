from django.apps import AppConfig
from django.conf import settings
from django.utils.autoreload import autoreload_started


def _observar_dotenv(sender, **kwargs):
    # O runserver só reinicia sozinho com arquivos .py; inclui o .env na observação.
    sender.watch_dir(settings.BASE_DIR, '.env')


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        autoreload_started.connect(_observar_dotenv)
