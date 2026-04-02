"""
Development settings — never use in production.
"""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Use console email in dev so you don't need an SMTP server
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relax cookie security in dev (HTTP, not HTTPS)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
