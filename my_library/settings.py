"""
Configurações do projeto My Library.

Valores sensíveis ou específicos de ambiente são lidos de variáveis de ambiente
(ou de um arquivo `.env` na raiz do projeto). Veja `.env.example`.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _carregar_dotenv(caminho: Path) -> None:
    """Carrega pares CHAVE=valor de um arquivo .env sem sobrescrever o ambiente."""
    if not caminho.is_file():
        return
    for linha in caminho.read_text(encoding='utf-8').splitlines():
        linha = linha.strip()
        if not linha or linha.startswith('#') or '=' not in linha:
            continue
        chave, valor = linha.split('=', 1)
        valor = valor.strip().strip('"').strip("'")
        if valor:  # "CHAVE=" vazio significa "usar o padrão"
            os.environ.setdefault(chave.strip(), valor)


def env_bool(nome: str, padrao: bool = False) -> bool:
    valor = os.environ.get(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in {'1', 'true', 'yes', 'on', 'sim'}


def env_list(nome: str, padrao: str = '') -> list[str]:
    return [item.strip() for item in os.environ.get(nome, padrao).split(',') if item.strip()]


_carregar_dotenv(BASE_DIR / '.env')


# ==================== SEGURANÇA ====================

DEBUG = env_bool('DJANGO_DEBUG', True)

_CHAVE_DEV = 'django-insecure-somente-para-desenvolvimento-local'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') or _CHAVE_DEV

if not DEBUG and SECRET_KEY == _CHAVE_DEV:
    raise ImproperlyConfigured('Defina DJANGO_SECRET_KEY quando DJANGO_DEBUG=False.')

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')

if not DEBUG:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'


# ==================== APLICAÇÕES ====================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'account',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'my_library.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.contagem_estantes',
            ],
        },
    },
]

WSGI_APPLICATION = 'my_library.wsgi.application'


# ==================== BANCO DE DADOS ====================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DJANGO_DB_PATH') or BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ==================== AUTENTICAÇÃO ====================

AUTHENTICATION_BACKENDS = [
    'account.backends.EmailOuUsuarioBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'account:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'account:login'


# ==================== INTERNACIONALIZAÇÃO ====================

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# ==================== ARQUIVOS ESTÁTICOS ====================

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ==================== CACHE ====================

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'my-library',
    }
}


# ==================== INTEGRAÇÕES ====================

# Opcional, mas recomendado: sem chave, o Google Books limita as requisições (HTTP 429)
# e a busca passa a usar a Open Library automaticamente.
GOOGLE_BOOKS_API_KEY = os.environ.get('GOOGLE_BOOKS_API_KEY', '')
BUSCA_CACHE_SEGUNDOS = int(os.environ.get('BUSCA_CACHE_SEGUNDOS', 60 * 60))
BUSCA_TIMEOUT_SEGUNDOS = float(os.environ.get('BUSCA_TIMEOUT_SEGUNDOS', 6))
