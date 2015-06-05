# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import django

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


SECRET_KEY = 'zrfxckyu67_26vav-c(utux0+f*lnt*e6ob9u+3mew_00x+gkb'
DEBUG = not os.path.exists(os.path.join(BASE_DIR, 'deploy'))
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ['examples.viewflow.io', '127.0.0.1']


# Application definition
INSTALLED_APPS = (
    # development
    'template_debug',
    # django apps
    'material',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # viewflow
    'viewflow',
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

if django.VERSION >= (1, 7):
    MIDDLEWARE_CLASSES += (
        'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    )

ROOT_URLCONF = 'tests.urls'


# Databases

import dj_database_url
DATABASES = {}

DATABASES['default'] = dj_database_url.config()
if not DATABASES['default']:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db{}{}.sqlite3'.format(django.VERSION[0], django.VERSION[1])),
    }

if django.VERSION >= (1, 7):
    DATABASES['default']['TEST'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db{}{}_test.sqlite3'.format(django.VERSION[0], django.VERSION[1]))
    }
else:
    DATABASES['default']['TEST_NAME'] = \
        os.path.join(BASE_DIR, 'db{}{}_test.sqlite3'.format(django.VERSION[0], django.VERSION[1]))



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
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.request',
    'tests.examples.website.users',
)

# Celery
INSTALLED_APPS += ('kombu.transport.django', )
BROKER_URL = 'django://'

CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'

CELERY_IMPORTS = [
    os.path.join(root, filename)[len(BASE_DIR)+1: -3].replace('/', '.')
    for root, dirs, files in os.walk(os.path.join(BASE_DIR, 'tests'))
    for filename in files
    if filename.startswith('test_') and filename.endswith('.py')]


# South
if django.VERSION < (1, 7):
    INSTALLED_APPS += ('south', )


# Jenkins
INSTALLED_APPS += ('django_jenkins',)
JENKINS_TASKS = (
    'django_jenkins.tasks.run_flake8',
    'django_jenkins.tasks.run_sloccount',
)

# shortcut for development
from django.template.base import add_to_builtins
add_to_builtins('template_debug.templatetags.debug_tags')

try:
    from tests.local_settings import *  # NOQA
except ImportError:
    pass


# import warnings
# warnings.filterwarnings("ignore",category=DeprecationWarning)
# warnings.filterwarnings('error')
