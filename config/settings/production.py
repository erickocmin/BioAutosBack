from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False
DATABASES = {"default": mysql_database_config()}  # noqa: F405
if SECRET_KEY == "unsafe-development-key-change-me":  # noqa: F405
    raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatoria en producción.")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)  # noqa: F405
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
