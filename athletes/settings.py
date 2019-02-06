"""
Django settings for Athletes project.
"""

import os

from datetime import timedelta
import requests
import google.cloud.logging
from google.cloud.logging.handlers.transports.sync import SyncTransport
from django.utils.log import DEFAULT_LOGGING as LOGGING

SITE_ENV_PREFIX = 'ATHLETES'


def get_env_var(name, default=''):
    """ Get all sensitive data from google vm custom metadata. """
    try:
        name = '_'.join([SITE_ENV_PREFIX, name])
        res = os.environ.get(name)
        if res:
            # Check env variable (Jenkins build).
            return res
        else:
            res = requests.get(
                'http://metadata.google.internal/computeMetadata/'
                'v1/instance/attributes/{}'.format(name),
                headers={'Metadata-Flavor': 'Google'}
            )
            if res.status_code == 200:
                return res.text
    except requests.exceptions.ConnectionError:
        return default
    return default


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = get_env_var(
    'SECRET_KEY',
    'qt3@x1(314ybu)d=)i1j$$q(&9wp$i9kwy0!_o9$z*ofr@^rd8'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = bool(get_env_var('DEBUG', 'True'))

INTERNAL_IPS = (
    '127.0.0.1',
)

ALLOWED_HOSTS = get_env_var('ALLOWED_HOSTS', '*').split(',')

ADMINS = [
    ('Mike', 'mriynuk@gmail.com'),
    ('Jamie', 'jaimedanderson@gmail.com'),
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',

    'django.contrib.humanize',
    'widget_tweaks',
    'easy_select2',
    'import_export',
    'rest_framework',
    'djstripe',
    'corsheaders',

    'core',
    'api',
]
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
if DEBUG:
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

ROOT_URLCONF = 'athletes.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'athletes.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': get_env_var('DB_NAME', 'athletes'),
        'USER': get_env_var('DB_USER', 'athletes_admin'),
        'PASSWORD': get_env_var('DB_PASSWORD', 'athletes_local_pass'),
        'HOST': get_env_var('DB_HOST', '127.0.0.1'),
        'PORT': '',
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://localhost:6379/9",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# CELERY STUFF
CELERY_BROKER_URL = 'redis://localhost:6379/9'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/9'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',  # TODO: remove latter
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    )
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('JWT',),
}

CORS_ORIGIN_WHITELIST = (
    'a.mkeda.me',
    'localhost:4200',
    '127.0.0.1:4200',
)

EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_PORT = 2525
EMAIL_HOST_USER = get_env_var('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = get_env_var('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
MAILGUN_SERVER_NAME = 'info.mkeda.me'
EMAIL_SUBJECT_PREFIX = '[Athletes]'
SERVER_EMAIL = 'admin@info.mkeda.me'

STRIPE_LIVE_PUBLIC_KEY = get_env_var('STRIPE_LIVE_PUBLIC_KEY')
STRIPE_LIVE_SECRET_KEY = get_env_var('STRIPE_LIVE_SECRET_KEY')
STRIPE_TEST_PUBLIC_KEY = get_env_var('STRIPE_TEST_PUBLIC_KEY')
STRIPE_TEST_SECRET_KEY = get_env_var('STRIPE_TEST_SECRET_KEY')
STRIPE_LIVE_MODE = False  # Change to True in production


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

MEDIA_URL = '/media/'

LOGIN_URL = '/login'

# Static files (CSS, JavaScript, Images)

STATIC_URL = 'https://storage.googleapis.com/cdn.mkeda.me/athletes/'
NO_AVATAR_IMAGE = STATIC_URL + 'img/no-avatar.png'
if DEBUG:
    STATIC_URL = '/static/'

STATICFILES_DIRS = (
    ('', os.path.join(BASE_DIR, 'static')),
)

STATIC_ROOT = '/home/voron/sites/cdn/athletes'


LOGGING['loggers']['athletes'] = {
    'handlers': ['django.server', 'mail_admins'],
    'level': 'INFO',
}
if not DEBUG:
    # StackDriver setup.
    # We need to use SyncTransport otherwise logs will not work for celery.
    client = google.cloud.logging.Client()
    LOGGING['handlers']['stackdriver'] = {
        'class': 'google.cloud.logging.handlers.CloudLoggingHandler',
        'client': client,
        'transport': SyncTransport,
    }
    LOGGING['loggers']['athletes']['handlers'].append('stackdriver')


GEOCODING_API_KEY = get_env_var('GEOCODING_API_KEY')

TWITTER_APP_KEY = get_env_var('TWITTER_APP_KEY')
TWITTER_APP_SECRET = get_env_var('TWITTER_APP_SECRET')
TWITTER_OAUTH_TOKEN = get_env_var('TWITTER_OAUTH_TOKEN')
TWITTER_OAUTH_TOKEN_SECRET = get_env_var('TWITTER_OAUTH_TOKEN_SECRET')

ALPHAVANTAGE_API_KEY = get_env_var('ALPHAVANTAGE_API_KEY')

AWS_ACCESS_ID = get_env_var('AWS_ACCESS_ID')
AWS_SECRET_ACCESS_KEY = get_env_var('AWS_SECRET_ACCESS_KEY')

DUEDIL_API_KEY = get_env_var('DUEDIL_API_KEY')


# Security
if not DEBUG:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
