"""
Django settings for simps_project project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for local development)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SECURITY SETTINGS ---
# Pull from Render environment variables; use a fallback ONLY for local dev
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-local-fallback-key')

# Converts the string 'True' or 'False' from environment variables to a boolean
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Dynamically add Render's URL to allowed hosts
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# --- APPLICATION DEFINITION ---
INSTALLED_APPS = [
    'user',
    'portfolio',
    'dashboard',
    'exploration', 
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise must be here
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'simps_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'simps_project.wsgi.application'

# --- DATABASE ---
# Using the variables you set in your Render environment tab
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'postgres'),
        'USER': os.getenv('DB_USER', 'postgres.qweqnmvwzivyeoyyzgzy'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Ocro3HnodXAAqmw8'),
        'HOST': os.getenv('DB_HOST', 'aws-1-ap-northeast-2.pooler.supabase.com'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# --- STATIC FILES ---
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles' 

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Production-only static file compression
if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# --- OTHER SETTINGS ---
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
SESSION_COOKIE_HTTPONLY = True