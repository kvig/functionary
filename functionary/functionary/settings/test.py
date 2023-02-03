from .base import *  # noqa

CELERY_BROKER_URL = "memory://"
CONSTANCE_BACKEND = "constance.backends.memory.MemoryBackend"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}
SECRET_KEY = "testsecret"
