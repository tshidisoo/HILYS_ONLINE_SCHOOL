"""HILYS ecosystem settings. Every secret comes from the environment; nothing that works in production has a default."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent.parent  # the HILYS repository root (holds materials/book1)
load_dotenv(BASE_DIR / ".env")


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"The environment variable {name} is missing.")
    return value


DEBUG = env("DJANGO_DEBUG", "0") == "1"
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-only-not-for-production" if DEBUG else None, required=True)
# Encrypts sensitive fields (children's support notes, dates of birth). Must be a Fernet key in production.
FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY", "Gx1o4Gk0cQm6bG0x2c8m8bH7vQ5m9V0Rk3t6o2W1y4E=" if DEBUG else None, required=True)
ALLOWED_HOSTS = [h for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "").split(",") if h]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "corsheaders",
    "common",
    "users",
    "audit",
    "settings_app",
    "catalogue",
    "leads",
    "families",
    "curriculum",
    "enrolments",
    "lessons",
    "pipeline",
    "billing",
    "finance",
    "teacherpay",
    "workflow",
    "privacy",
    "analytics",
    "website",
    "mobile",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {"default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": env("POSTGRES_DB", "hilys"),
    "USER": env("POSTGRES_USER", "hilys"),
    "PASSWORD": env("POSTGRES_PASSWORD", "hilys-dev" if DEBUG else None, required=True),
    "HOST": env("POSTGRES_HOST", "127.0.0.1"),
    "PORT": env("POSTGRES_PORT", "5432"),
}}

AUTH_USER_MODEL = "users.User"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
]

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "UTC"  # the server runs in UTC; business time is BUSINESS_TIME_ZONE
USE_TZ = True
USE_I18N = True
BUSINESS_TIME_ZONE = "Africa/Harare"
DEFAULT_CURRENCY = "USD"

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"  # private: served only through authenticated views
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["users.auth.ActiveTokenAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.Pagination",
    "DEFAULT_THROTTLE_RATES": {"public": "20/hour", "login": "10/minute"},
    "EXCEPTION_HANDLER": "common.errors.plain_exception_handler",
}

# CORS is an allow-list. Allow-all only in debug with no list set.
CORS_ALLOWED_ORIGINS = [o for o in env("CORS_ALLOWED_ORIGINS", "").split(",") if o]
CORS_ALLOW_ALL_ORIGINS = DEBUG and not CORS_ALLOWED_ORIGINS

CELERY_BROKER_URL = env("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_TIMEZONE = BUSINESS_TIME_ZONE
CELERY_BEAT_SCHEDULE = {
    "late-leads": {"task": "workflow.tasks.remind_late_leads", "schedule": 60 * 60},
    "overdue-invoices": {"task": "workflow.tasks.remind_overdue_invoices", "schedule": 60 * 60 * 24},
    "expiring-quotes": {"task": "workflow.tasks.remind_expiring_quotes", "schedule": 60 * 60 * 24},
    "next-month-lessons": {"task": "lessons.tasks.schedule_next_month", "schedule": 60 * 60 * 24},
}

# Outward channels stay off until the owner supplies credentials.
EMAIL_ENABLED = env("EMAIL_ENABLED", "0") == "1"
PUSH_ENABLED = env("PUSH_ENABLED", "0") == "1"
CARD_PAYMENTS_ENABLED = env("STRIPE_SECRET_KEY") is not None
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend" if EMAIL_ENABLED else "django.core.mail.backends.console.EmailBackend"

PUBLIC_SITE_URL = env("PUBLIC_SITE_URL", "http://localhost:5500")
API_PUBLIC_URL = env("API_PUBLIC_URL", "http://localhost:8000")

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_SSL_REDIRECT = True
