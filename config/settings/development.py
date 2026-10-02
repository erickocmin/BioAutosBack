from .base import *  # noqa: F403

DEBUG = env.bool("DJANGO_DEBUG", default=True)  # noqa: F405

# El huellero accede mediante la IP LAN, que puede cambiar entre redes. Esta
# apertura solo existe en desarrollo; producción conserva ALLOWED_HOSTS estricto.
if env.bool("ALLOW_LAN_DEV_SERVER", default=True):  # noqa: F405
    ALLOWED_HOSTS = ["*"]

if env.bool("USE_SQLITE", default=True):  # noqa: F405
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}  # noqa: F405
else:
    DATABASES = {"default": mysql_database_config()}  # noqa: F405
