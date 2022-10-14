import os
import django
import environ
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'
BASE_DIR = Path(__file__).resolve(strict=True).parents[1]

# configure django-environ to run in dev mode without .env file
env = environ.Env(
    DATABASE_URL=(str, 'sqlite:///' + str(BASE_DIR) + '/db{}{}.sqlite3'.format(*django.VERSION[:2])),
    DOMAIN_NAME=(str, '127.0.0.1'),
    DEBUG=(bool, False),
    SECRET_KEY=(str, '--secret--'),
)
env.read_env(BASE_DIR / '.env') if os.path.exists(BASE_DIR / '.env') else None

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG')

ALLOWED_HOSTS = [env.str('DOMAIN_NAME')]


# Application definition

INSTALLED_APPS = [
    'tests.apps.TestsConfig',
    'viewflow',
    'viewflow.workflow',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'guardian',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = None

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

# Auth

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend'
)

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases
DATABASES = {
    'default': env.db(),
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

# Disable migrations for tests
MIGRATION_MODULES = {
    'viewflow': None,
    'admin': None,
    'auth': None,
    'contenttypes': None,
    'sessions': None,
    'messages': None,
    'staticfiles': None,
    'tests': None,
    'guardian': None,
    'helloworld': None,
    'bloodtest': None,
}

# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_URL = '/static/'

STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_ROOT = BASE_DIR / '..' / '.media'

MEDIA_URL = '/media/'

# Loggin
# https://docs.djangoproject.com/en/2.0/topics/logging/

LOGGING = {
    'version': 1,
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        }
    }
}

# Fixtures
# https://docs.djangoproject.com/en/2.0/howto/initial-data/

FIXTURE_DIRS = (
    BASE_DIR / 'fixtures',
)

# Celery
# http://docs.celeryproject.org/en/latest/index.html

CELERY_WORKER_CONCURRENCY = 1
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_BROKER_URL = 'redis://localhost:6379/10'

CELERY_IMPORTS = [
    os.path.join(root, filename)[len(str(BASE_DIR)) + 1: -3].replace('/', '.')
    for root, dirs, files in os.walk(BASE_DIR / 'tests')
    for filename in files
    if filename.startswith('test_') and filename.endswith('.py')
]
