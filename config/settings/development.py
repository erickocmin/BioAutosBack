from .base import *  # noqa: F403

DEBUG = env.bool("DJANGO_DEBUG", default=True)  # noqa: F405

if env.bool("USE_SQLITE", default=False):  # noqa: F405
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}  # noqa: F405
else:
    DATABASES = {"default": mysql_database_config()}  # noqa: F405
