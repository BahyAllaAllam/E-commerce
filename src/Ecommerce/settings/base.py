"""
Base settings shared across all environments.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ['SECRET_KEY']  # No fallback — fail loudly if missing

INSTALLED_APPS = [
    # My Apps
    'users.apps.UsersConfig',
    'store.apps.StoreConfig',
    'bootstrap4',
    'phone_field',
    'django_countries',
    # REST framework
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',
    # Allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    # dj-rest-auth
    'dj_rest_auth',
    'dj_rest_auth.registration',
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Required by allauth
    'django.contrib.sites',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'Ecommerce.urls'

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
                'store.context_processors.cart_items',
            ],
        },
    },
]

WSGI_APPLICATION = 'Ecommerce.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Fixed: was [BASE_DIR, "static"]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD', '')

# Auth redirects (single declaration)
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Allauth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_USERNAME_BLACKLIST = ['admin', 'user', 'users', 'account', 'accounts']
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_CHANGE_EMAIL = True
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 1
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = True
ACCOUNT_SIGNUP_FORM_HONEYPOT_FIELD = True
ACCOUNT_EMAIL_NOTIFICATIONS = True
ACCOUNT_MAX_EMAIL_ADDRESSES = 2

# DRF
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 5,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# PayPal — set in environment, not hardcoded
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')

# Used by PayPal return URLs — must be set in env for production
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')
