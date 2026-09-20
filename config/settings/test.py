from .base import *  # noqa: F403

DEBUG = False
if env.bool("TEST_USE_MYSQL", default=False):  # noqa: F405
    DATABASES = {"default": mysql_database_config()}  # noqa: F405
    DATABASES["default"]["NAME"] = env("TEST_DB_NAME", default="sisgetran_test")  # noqa: F405
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
