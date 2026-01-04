from .base import *

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0", "*"]

# Database - Use SQLite for quick local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='acadai_dev'),
#         'USER': config('DB_USER', default='acadai_user'),
#         'PASSWORD': config('DB_PASSWORD', default='devpassword'),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }
#


SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Django Debug Toolbar
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# DEBUG_TOOLBAR_CONFIG = {
#     "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
# }

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Disable rate limiting in development for easier testing
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "10000/hour",
    "user": "10000/hour",
    "submission": "10000/hour",
}

# More verbose logging in development
LOGGING["loggers"]["apps"]["level"] = "DEBUG"
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["django.db.backends"] = {
    "handlers": ["console"],
    "level": "DEBUG",  # Set to INFO to reduce query logging
    "propagate": False,
}

# Cache - Use local memory cache in development
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Celery - Use eager execution in development (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Static files - simpler setup for development
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files - local storage
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

# Development-specific Django extensions
try:
    import django_extensions

    INSTALLED_APPS += ["django_extensions"]
    SHELL_PLUS = "ipython"
    SHELL_PLUS_PRINT_SQL = True
except ImportError:
    pass

# Disable template caching in development
TEMPLATES[0]["OPTIONS"]["debug"] = True

# Allow weak passwords in development (for testing)
AUTH_PASSWORD_VALIDATORS = []

# Show SQL queries in console (optional - can be noisy)
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"

# Development secret key (change in production!)
SECRET_KEY = config(
    "SECRET_KEY",
    default="django-insecure-is)y%#b#ze+0j_g8dik+^tmw_z6#e)ryc3nl*&l+v1nlav)3e8",
)

# Grading service - use mock by default
GRADING_SERVICE_TYPE = "mock"

print("=" * 60)
print("🔧 DEVELOPMENT MODE ACTIVE")
print("=" * 60)
print(f"DEBUG: {DEBUG}")
print(f"Database: {DATABASES['default']['ENGINE']}")
print(f"Allowed Hosts: {ALLOWED_HOSTS}")
print("=" * 60)
