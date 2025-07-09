"""Test settings for devops_pipeline project."""

import os
import sys

from .base import *  # noqa

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

# Simplified logging for tests - console only to avoid file permission issues in CI
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "devops_pipeline": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}

# Celery settings for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Security settings for tests
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]
