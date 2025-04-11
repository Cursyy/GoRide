"""
Django settings for GoRide project.

Generated by 'django-admin startproject' using Django 5.1.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path
import os
import datetime
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = (
    "django-insecure-9t=ttb$u6z-4qv6x)sfl!fh%-p!^qq657nlr(xct5gu88mp7k!"  # noqa: E501
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    # project apps
    "daphne",
    "channels",
    "accounts",
    # default apps
    "jazzmin",
    "silk",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "wallet.apps.WalletConfig",
    # project apps
    "main",
    "support",
    "find_transport",
    "payments",
    "subscriptions",
    "vouchers",
    "booking",
    "get_direction",
    "avatar",
    # third party apps
    "crispy_forms",
    "crispy_bootstrap5",
    "paypal.standard.ipn",
]
ASGI_APPLICATION = "GoRide.asgi.application"
CRISPY_TEMPLATE_PACK = "bootstrap5"


CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}

MIDDLEWARE = [
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "silk.middleware.SilkyMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

INTERNAL_IPS = [
    "127.0.0.1",
]
ROOT_URLCONF = "GoRide.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "get_direction.context_processors.active_trip",
                "wallet.context_proccesors.wallet_balance",
                "main.context_processors.location_context",
            ],
        },
    },
]

WSGI_APPLICATION = "GoRide.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.environ.get("POSTGRES_DB", "goride_db"),
#         'USER': os.environ.get("POSTGRES_USER", "goride_user"),
#         'PASSWORD': os.environ.get("POSTGRES_PASSWORD", "yourpassword"),
#         'HOST': os.environ.get("POSTGRES_HOST", "db"),
#         'PORT': os.environ.get("POSTGRES_PORT", "5432"),
#     }
# }

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://redis:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# celery config
# https://docs.celeryq.dev/en/latest/django/first-steps-with-django.html
CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://redis:6379/0")

CELERY_BEAT_SCHEDULER = "django_celery_beat.scheduler:DatabaseScheduler"
CELERY_ACCEPT_TOKEN = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ["application/json"]
# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # noqa: E501
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # noqa: E501
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGES = (("en", ("English")), ("ga", ("Gaeilge")), ("uk", ("Українська")))

LANGUAGE_CODE = "en-us"

# MODELTRANSLATION_DEFAULT_LANGUAGE = "en"
# MODELTRANSLATION_LANGUAGES = ("en", "ga", "uk")

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

LOCALE_PATHS = [
    os.path.join(BASE_DIR, "locale"),
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "static/"
STATICFILES_DIRS = [str(BASE_DIR.joinpath("static"))]
STATIC_ROOT = str(BASE_DIR.joinpath("staticfiles"))
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom settings
AUTH_USER_MODEL = "accounts.CustomUser"

LOGIN_REDIRECT_URL = "main:home"
LOGOUT_REDIRECT_URL = "main:home"


LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] [%(message)s] [%(funcName)s()] [%(lineno)d] [%(pathname)s]"
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": os.path.join(
                LOG_DIR, f"{datetime.datetime.now().strftime('%Y-%m-%d')}_errors.log"
            ),
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "WARNING",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

PAYPAL_TEST = True
PAYPAL_MODE = "sandbox"
PAYPAL_CLIENT_ID = config("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = config("PAYPAL_CLIENT_SECRET")
PAYPAL_RECEIVER_EMAIL = "sb-yfvxa37272511@business.example.com"

STRIPE_PUBLIC_KEY = config("STRIPE_PUBLIC_KEY")
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY")


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_FROM = "tud.goride@gmail.com"
EMAIL_HOST_USER = "tud.goride@gmail.com"
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True

PASSWORD_RESET_TIMEOUT = 60 * 60 * 4

CUSTOM_CSS_PATH = "admin/admin.css"
SITE_LOGO_PATH = "admin/logo.png"


# Jazzmin admin theme
# https://django-jazzmin.readthedocs.io/configuration/

JAZZMIN_SETTINGS = {
    "custom_css": CUSTOM_CSS_PATH,
    # Site name
    "site_title": "GoRide Admin",
    "site_header": "GoRide Admin",
    "site_brand": "GoRide Admin Panel",
    "site_logo": SITE_LOGO_PATH,
    "site_logo_classes": "img-circle",
    # Copyright
    "copyright": "GoRide Ltd",
    #############
    # UI / Theme #
    #############
    # Set LIGHT theme by default
    "theme": "flatly",  # Or another light theme: "litera", "pulse", "simplex", "yeti"
    # Set DARK theme for the switcher
    "dark_mode_theme": "darkly",  # Or another dark theme: "cyborg", "slate"
    "show_ui_builder": True,  # Allows the user to change the theme via UI
    ###############
    # Navigation  #
    ###############
    "show_sidebar": True,
    "language_chooser": True,
    "navigation_expanded": True,
    # Sorting order (check app names!)
    "order_with_respect_to": [
        # User management
        "accounts",  # App for CustomUser
        "auth",  # Default auth (for Group, if used)
        "subscriptions",
        "support",
        # Transport operations
        "get_direction",
        "find_transport",
        # Finance
        "wallet",
        "vouchers",
        "booking",
        "payments",  # Added payments if it should be in the admin panel
        "paypal.standard.ipn",  # Added PayPal IPN if needed
    ],
    # Icons (FIXED CustomUser, check other models!)
    "icons": {
        "accounts": "fas fa-user-circle",
        "accounts.customuser": "fas fa-user",  # Model name in lowercase
        "auth": "fas fa-users-cog",  # For default auth (if Group is needed)
        "auth.group": "fas fa-users",
        "subscriptions": "fas fa-id-card",
        "support": "fa-regular fa-comment",
        "get_direction": "fas fa-directions",
        "get_direction.trip": "fas fa-route",
        "get_direction.route": "fas fa-map-marked-alt",
        "find_transport": "fas fa-search-location",
        "find_transport.vehicles": "fa-solid fa-bicycle",  # Example icon for Vehicles
        "wallet": "fa-solid fa-money-bill",
        "vouchers": "fas fa-ticket-alt",
        "vouchers.voucher": "fas fa-receipt",  # Example
        "booking": "fas fa-calendar-check",
        "booking.booking": "fas fa-book-open",  # Example
        "payments": "fas fa-credit-card",  # Example
        "paypal.standard.ipn.paypalipn": "fab fa-paypal",  # Example
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    #################
    # Related Modal #
    #################
    "related_modal_active": True,
    #############
    # Links     #
    #############
    "topmenu_links": [
        # Link to the main site page (check the URL name 'main:home')
        {"name": "Back to Site", "url": "main:home", "new_window": False},
        {"name": "Screening", "url": "/silk/", "new_window": True},
    ],
    #############
    # Forms     #
    #############
    "changeform_format": "horizontal_tabs",
}

# UI Tweaks settings remain the same, but now they will
# apply to the default light theme.
# The dark theme "darkly" has its own styles that may override some tweaks.
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-warning",
    "navbar": "navbar-gray navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "cyborg",
    "dark_mode_theme": "cyborg",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
    "actions_sticky_top": True,
}
