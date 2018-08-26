"""
Django settings for athletes project.
"""

import requests
import os

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
    ('Mike', 'mriynuk@gmail.com')
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'widget_tweaks',
    'easy_select2',
    'import_export',

    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

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

STATIC_URL = '/static/' if DEBUG else 'https://cdn.mkeda.me/athletes/'

STATICFILES_DIRS = (
    ('', os.path.join(BASE_DIR, 'static')),
)

STATIC_ROOT = '/home/voron/sites/cdn/athletes'

# Security
if  DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_PRELOAD = True
