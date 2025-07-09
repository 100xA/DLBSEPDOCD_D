"""Test settings for devops_pipeline project."""

import os
import sys

from .base import *  # noqa
from .base import LOGGING

# Determine if running integration tests
is_integration_test = any("tests/integration" in arg for arg in sys.argv)

# Test database settings
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("TEST_DB_NAME", "devops_test"),
        "USER": os.getenv("TEST_DB_USER", "devops_user"),
        "PASSWORD": os.getenv("TEST_DB_PASSWORD", "devops_password"),
        "HOST": os.getenv("TEST_DB_HOST", "localhost"),
        "PORT": os.getenv("TEST_DB_PORT", "5433"),
        "TEST": {
            "NAME": "test_devops_pipeline",
        },
    }
}

# Use in-memory SQLite for faster unit tests
if not is_integration_test:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }

# Redis for tests
REDIS_URL = os.getenv("TEST_REDIS_URL", "redis://localhost:6380/0")
CELERY_BROKER_URL = REDIS_URL
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Cache settings for tests
if is_integration_test:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        }
    }


# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Password hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Media files for tests
DEFAULT_FILE_STORAGE = "django.core.files.storage.InMemoryStorage"

# Logging for tests
LOGGING["loggers"]["devops_pipeline"]["level"] = "WARNING"
LOGGING["loggers"]["django"]["level"] = "WARNING"

# Celery settings for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Security settings for tests
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
