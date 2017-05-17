import os
import configparser

import easypost
import stripe

# the path of the top level folder for this site, e.g. /var/lib/www/w3
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the path of the folder containing this file
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = False

# -- Secret keys --
# Load keys that can't be added to the repo for security reasons
config = configparser.ConfigParser()
config.read(os.path.join(BASE_DIR, 'keys.txt'))

SECRET_KEY = config['django']['secret_key']

if DEBUG:
    STRIPE_PRIVATE = config['stripe']['test']
    easypost.api_key = config['easypost']['test']
else:
    STRIPE_PRIVATE = config['stripe']['prod']
    easypost.api_key = config['easypost']['prod']

ALLOWED_HOSTS = ['wcubed.co', 'www.wcubed.co', '127.0.0.1',]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # actual apps
    'account',
    'cart',
    'checkout',
    'w3',
    'shop_manager'
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

ROOT_URLCONF = 'w3.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'w3.wsgi.application'

# ToDo: Email
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'wcubedcompany@gmail.com'
EMAIL_HOST_PASSWORD = '0MDLVs8IDwGs'
EMAIL_USE_TLS = True

# production database is MySQL, but it's okay to use SQLite for development
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'wcubed',
            'USER': config['mysql']['username'],
            'PASSWORD': config['mysql']['password'],
            'HOST': 'localhost',
            'PORT': '',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'EST'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

# where new uploaded media files get put and served from
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

MEDIA_URL = '/media/'

# the unified location from which to serve files in production
STATIC_ROOT = os.path.join(BASE_DIR, "static")

STATIC_URL = '/static/'

# temporary directories for serving files in development
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "cart/static"),
    os.path.join(BASE_DIR, "w3/static")
    ]