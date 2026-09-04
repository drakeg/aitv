import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-key-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', 'true').lower() in {'1', 'true', 'yes', 'on'}
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
    if host.strip()
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'content',
    'watchlist',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'streamhub.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'streamhub.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

EMAIL_HOST = os.getenv('SMTP_HOST', '').strip()
EMAIL_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_HOST_USER = os.getenv('SMTP_USERNAME', '').strip()
EMAIL_HOST_PASSWORD = os.getenv('SMTP_PASSWORD', '').strip()
EMAIL_USE_TLS = os.getenv('SMTP_USE_TLS', 'true').lower() in {'1', 'true', 'yes', 'on'}
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER or 'aitv@localhost')
RELEASE_EMAIL_CONFIGURED = bool(EMAIL_HOST and DEFAULT_FROM_EMAIL)
EMAIL_BACKEND = (
    'django.core.mail.backends.smtp.EmailBackend'
    if RELEASE_EMAIL_CONFIGURED
    else 'django.core.mail.backends.locmem.EmailBackend'
)
