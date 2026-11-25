"""
Django settings for Nexgrad project.
The Engineering Career Intelligence & Opportunity Platform.
"""

from pathlib import Path
import os
import sys

# Build paths inside the project: BASE_DIR is backend/, PROJECT_ROOT is repository root
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / 'frontend'
AI_SERVICE_DIR = PROJECT_ROOT / 'ai-service'

# Register AI service and backend directories in Python path
for extra_path in [str(AI_SERVICE_DIR), str(BASE_DIR)]:
    if extra_path not in sys.path:
        sys.path.insert(0, extra_path)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
    load_dotenv(PROJECT_ROOT / '.env')
    if os.path.exists('/etc/nexgrad/nexgrad.env'):
        load_dotenv('/etc/nexgrad/nexgrad.env')
except ImportError:
    pass

SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-nexgrad-career-intelligence-academic-eval-30marks'
)

DEBUG = os.environ.get('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['*']

# Administrator and SRE Alert Email Notification Recipients
ADMINS = [('Karthik SN', os.environ.get('ALERT_EMAIL', 'karthiksn20112004@gmail.com'))]
MANAGERS = ADMINS

# Application definition

INSTALLED_APPS = [
    # Core Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Nexgrad modular domain apps
    'accounts.apps.AccountsConfig',
    'core.apps.CoreConfig',
    'students.apps.StudentsConfig',
    'recruiters.apps.RecruitersConfig',
    'institutions.apps.InstitutionsConfig',
    'jobs.apps.JobsConfig',
    'applications.apps.ApplicationsConfig',
    'assessments.apps.AssessmentsConfig',
    'career_intelligence.apps.CareerIntelligenceConfig',
    'notifications.apps.NotificationsConfig',
    'challenges.apps.ChallengesConfig',
    'ai_assistant.apps.AiAssistantConfig',
]

# Custom User Model with Multi-Role support (Student, Recruiter, Institution, Admin)
AUTH_USER_MODEL = 'accounts.CustomUser'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'nexgrad.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            FRONTEND_DIR / 'templates',
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.brand_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'nexgrad.wsgi.application'
ASGI_APPLICATION = 'nexgrad.asgi.application'

# Database Configuration
# Supports MySQL (XAMPP / phpMyAdmin), PostgreSQL (EC2 production), or SQLite fallback
DB_ENGINE_CONFIG = os.environ.get('DB_ENGINE', 'mysql').lower()

if DB_ENGINE_CONFIG in ('mysql', 'mariadb'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'nexgrad'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                'charset': 'utf8mb4',
            }
        }
    }
elif DB_ENGINE_CONFIG in ('postgres', 'postgresql'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'nexgrad'),
            'USER': os.environ.get('DB_USER', 'nexgrad_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    FRONTEND_DIR / 'static',
] if (FRONTEND_DIR / 'static').exists() else [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads: Resumes, Profile avatars, Company logos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'core:home'
LOGOUT_REDIRECT_URL = 'core:home'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Google Gemini AI Integration for VEX Career Companion
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')


