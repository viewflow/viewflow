# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))


SECRET_KEY = 'zrfxckyu67_26vav-c(utux0+f*lnt*e6ob9u+3mew_00x+gkb'
DEBUG = not os.path.exists(os.path.join(BASE_DIR, 'deploy'))
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['examples.viewflow.io', '127.0.0.1']


# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # viewflow
    'viewflow',
    'viewflow.site',
    # Tests
    'tests.unit',
    'tests.integration',
    # Examples
    'tests.examples.shipment',
    'tests.examples.helloworld',
    'tests.examples.customnode',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'tests.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3')
    }
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = False


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'tests/static'),
)

STATIC_ROOT = os.path.join(BASE_DIR, 'deploy/static')

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'tests/templates'),
)

from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS
TEMPLATE_CONTEXT_PROCESSORS = TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'tests.examples.website.users',
)

# Celery
import djcelery
djcelery.setup_loader()

BROKER_URL = 'django://'
INSTALLED_APPS += ('kombu.transport.django', 'djcelery')
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'

try:
    from tests.local_settings import *  # NOQA
except ImportError:
    pass
