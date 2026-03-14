"""
===========================================
School Financial Management System
Base Settings (shared across all environments)
===========================================
"""

import os
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

# -----------------------------------------------
# PATH CONFIGURATION
# -----------------------------------------------
# Build paths: BASE_DIR = school_fms/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# -----------------------------------------------
# SECURITY
# -----------------------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# -----------------------------------------------
# APPLICATION DEFINITION
# -----------------------------------------------
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',  # For formatting numbers/dates in templates
]

THIRD_PARTY_APPS = [
    'rest_framework',           # Django REST Framework
    'rest_framework_simplejwt', # JWT Authentication
    'corsheaders',              # CORS headers for API
    'django_filters',           # Filtering for API views
]

LOCAL_APPS = [
    'apps.users',                   # Authentication, RBAC, Audit Trail
    'apps.general_ledger',          # Chart of Accounts, Journal Entries
    'apps.accounts_receivable',     # Student Invoicing, Payments
    'apps.accounts_payable',        # Vendor Management, Expenses
    'apps.reports',                 # Financial Reports, Budgets
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# -----------------------------------------------
# MIDDLEWARE
# -----------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',          # CORS (must be before CommonMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',      # CSRF protection
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.AuditTrailMiddleware',      # Custom audit logging
]

# -----------------------------------------------
# URL CONFIGURATION
# -----------------------------------------------
ROOT_URLCONF = 'config.urls'

# -----------------------------------------------
# TEMPLATE CONFIGURATION
# -----------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Project-level templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.users.context_processors.user_permissions',
            ],
        },
    },
]

# -----------------------------------------------
# WSGI / ASGI
# -----------------------------------------------
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# -----------------------------------------------
# DATABASE (MySQL)
# Override in development.py for SQLite fallback
# -----------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME', default='school_fms'),
        'USER': config('DB_USER', default='root'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='127.0.0.1'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",  # Enforce strict SQL
        },
        # Use persistent connections to reduce overhead
        'CONN_MAX_AGE': 600,
    }
}

# -----------------------------------------------
# CUSTOM USER MODEL
# -----------------------------------------------
AUTH_USER_MODEL = 'users.CustomUser'

# -----------------------------------------------
# PASSWORD VALIDATION
# -----------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------------------------
# INTERNATIONALIZATION
# -----------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------
# STATIC FILES (CSS, JavaScript, Images)
# -----------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # Dev: look in project-level static/
STATIC_ROOT = BASE_DIR / 'staticfiles'    # Prod: collectstatic output

# -----------------------------------------------
# MEDIA FILES (User uploads: receipts, etc.)
# -----------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------
# DEFAULT PRIMARY KEY
# -----------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------
# DJANGO REST FRAMEWORK
# -----------------------------------------------
REST_FRAMEWORK = {
    # Use JWT as default authentication
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # For browsable API & templates
    ),
    # Require authentication by default (override per-view if needed)
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # Filtering and pagination
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    # Date/time formatting
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    # Exception handler
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# -----------------------------------------------
# JWT CONFIGURATION (Simple JWT)
# -----------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        days=config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7, cast=int)
    ),
    'ROTATE_REFRESH_TOKENS': True,           # Issue new refresh token on refresh
    'BLACKLIST_AFTER_ROTATION': True,         # Blacklist old refresh tokens
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_OBTAIN_SERIALIZER': 'apps.users.serializers.CustomTokenObtainPairSerializer',
}

# -----------------------------------------------
# CORS SETTINGS
# -----------------------------------------------
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL', default=True, cast=bool)  # Dev only
CORS_ALLOW_CREDENTIALS = True

# -----------------------------------------------
# SECURITY SETTINGS
# -----------------------------------------------
# These are enhanced in production.py
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking
SECURE_CONTENT_TYPE_NOSNIFF = True

# -----------------------------------------------
# LOGIN CONFIGURATION (for template-based views)
# -----------------------------------------------
LOGIN_URL = '/auth/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/auth/login/'

# -----------------------------------------------
# BACKUP CONFIGURATION
# -----------------------------------------------
BACKUP_DIR = config('BACKUP_DIR', default=str(BASE_DIR / 'backups'))

# -----------------------------------------------
# LOGGING
# -----------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'fms.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
