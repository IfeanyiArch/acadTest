from .base import *

DEBUG = False

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": ":memory:",
#         "TEST": {
#             "NAME": ":memory:",
#         },
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="acad_test"),
        "USER": config("DB_USER", default="user"),
        "PASSWORD": config("DB_PASSWORD", default="devpassword"),
        "HOST": "acad_db_test",
        "PORT": config("DB_PORT", default="5432"),
    }
}


class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = {"authentication": None, "assessment": None, "auth": None}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = []

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"
CELERY_RESULT_BACKEND = "cache+memory://"

# Disable throttling in tests
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "1000000/hour",
    "user": "1000000/hour",
    "submission": "1000000/hour",
}

# Remove authentication requirement for easier testing (optional)
# REST_FRAMEWORK['DEFAULT_PERMISSION_CLASSES'] = []

REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
    "rest_framework.authentication.TokenAuthentication",
]

# Static files - Simplified for tests
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"
STATIC_ROOT = BASE_DIR / "test_static"

# Media files - Use temporary directory
MEDIA_ROOT = BASE_DIR / "test_media"

# Logging - Minimal logging during tests
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

# Security settings - Relaxed for tests
SECRET_KEY = "test-secret-key-not-for-production"
ALLOWED_HOSTS = ["*"]

# Disable HTTPS requirements
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0

# CORS - Allow all for tests
CORS_ALLOW_ALL_ORIGINS = True

# Grading service - Always use mock in tests
GRADING_SERVICE_TYPE = "mock"

# Test-specific settings
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Coverage settings (if using coverage.py)
COVERAGE_MODULE_EXCLUDES = [
    "tests$",
    "settings$",
    "urls$",
    "locale$",
    "migrations",
    "fixtures",
    "admin$",
    "django_extensions",
]

# Pytest settings (if using pytest-django)
PYTEST_ARGS = [
    "--verbose",
    "--strict-markers",
    "--tb=short",
    "--cov=apps",
    "--cov-report=term-missing",
    "--cov-report=html",
]

# Factory Boy settings
FACTORY_FOR_DJANGO_GET_OR_CREATE = True

# Disable template caching in tests
TEMPLATES[0]["OPTIONS"]["debug"] = True
if "loaders" in TEMPLATES[0]["OPTIONS"]:
    del TEMPLATES[0]["OPTIONS"]["loaders"]

# Use console output for easier debugging during tests
# Set to True to see print statements during tests
TEST_OUTPUT_VERBOSE = False

if TEST_OUTPUT_VERBOSE:
    LOGGING["loggers"]["django"]["level"] = "DEBUG"
    LOGGING["loggers"]["apps"]["level"] = "DEBUG"

print("=" * 60)
print("🧪 TEST MODE ACTIVE")
print("=" * 60)
print(f"Database: {DATABASES['default']['ENGINE']}")
print(f"Database Name: {DATABASES['default']['NAME']}")
print(f"Celery Eager: {CELERY_TASK_ALWAYS_EAGER}")
print("=" * 60)
