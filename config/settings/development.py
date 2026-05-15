"""
===========================================
Development Settings
===========================================
Overrides for local development environment.
Uses SQLite as fallback if MySQL is unavailable.
"""

from .base import *  # noqa: F401, F403

# -----------------------------------------------
# DEBUG MODE
# -----------------------------------------------
DEBUG = True

# Always allow local hosts (production .env may omit 127.0.0.1)
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '[::1]']

# -----------------------------------------------
# DATABASE (SQLite fallback for quick dev setup)
# -----------------------------------------------
# SQLite for development (no MySQL required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# -----------------------------------------------
# EMAIL (Console backend for development)
# -----------------------------------------------
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# -----------------------------------------------
# CORS (Allow all origins in development)
# -----------------------------------------------
CORS_ALLOW_ALL_ORIGINS = True

# -----------------------------------------------
# LOGGING (More verbose in development)
# -----------------------------------------------
LOGGING['root']['level'] = 'DEBUG'
