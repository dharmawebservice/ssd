from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ==================================================
# SECURITY
# ==================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-development-key"
)

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1,ssd-524c.onrender.com"
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1:8000,http://localhost:8000"
).split(",")

# ==================================================
# APPLICATIONS
# ==================================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    # "cloudinary_storage",          # must be BEFORE staticfiles
    "django.contrib.staticfiles",
    # "cloudinary",
    "web",
]

# ==================================================
# MIDDLEWARE
# ==================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nursery.urls"

# ==================================================
# TEMPLATES
# ==================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "web.context_processors.user_profile",
                "web.context_processors.cart_count",
            ],
        },
    },
]

WSGI_APPLICATION = "nursery.wsgi.application"

# ==================================================
# DATABASE
# ==================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20,
        },
    }
}

# ==================================================
# AUTH
# ==================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LOGIN_URL = "/auth/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# ==================================================
# SESSIONS
# ==================================================

SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30

# ==================================================
# CACHE
# ==================================================

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ssd-nursery",
        "TIMEOUT": 300,
    }
}

# ==================================================
# INTERNATIONALIZATION
# ==================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ==================================================
# STATIC FILES
# ==================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Do NOT define STATICFILES_DIRS

STATIC_ROOT = BASE_DIR / "staticfiles"


# ==================================================
# MEDIA FILES
# ==================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==================================================
# CLOUDINARY
# ==================================================

# CLOUDINARY_STORAGE = {
#     "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME"),
#     "API_KEY":    os.getenv("CLOUDINARY_API_KEY"),
#     "API_SECRET": os.getenv("CLOUDINARY_API_SECRET"),
# }

# ==================================================
# STORAGE BACKENDS  (Django 4.2 style)
# Using plain StaticFilesStorage for both dev and prod
# to avoid WhiteNoise crashing on duplicate/missing files.
# WhiteNoiseMiddleware in MIDDLEWARE already serves static
# files efficiently without needing the manifest storage.
# ==================================================

# STORAGES = {
#     "default": {
#         "BACKEND": (
#             "cloudinary_storage.storage.MediaCloudinaryStorage"
#             if not DEBUG
#             else "django.core.files.storage.FileSystemStorage"
#         ),
#     },
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
#     },
# }

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}
# ==================================================
# EMAIL  (Brevo SMTP)
# ==================================================

EMAIL_BACKEND       = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST          = os.getenv("EMAIL_HOST", "smtp-relay.brevo.com")
EMAIL_PORT          = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER     = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS       = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_USE_SSL       = os.getenv("EMAIL_USE_SSL", "False") == "True"

DEFAULT_FROM_EMAIL  = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "ssdnurserygarden@gmail.com"
)

BREVO_API_KEY = os.getenv("BREVO_API_KEY")

# ==================================================
# SITE URL  (used in order modification emails)
# ==================================================

SITE_URL = os.getenv("SITE_URL", "https://ssd-524c.onrender.com")

# ==================================================
# PAYMENTS
# ==================================================

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# ==================================================
# DEFAULT PRIMARY KEY
# ==================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==================================================
# LOGGING
# ==================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "web": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}