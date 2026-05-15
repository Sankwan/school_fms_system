"""
===========================================
Production Settings
===========================================
Security-hardened settings for production deployment.
"""

from .base import *  # noqa: F401, F403

# -----------------------------------------------
# DEBUG OFF
# -----------------------------------------------
DEBUG = False

# -----------------------------------------------
# STATIC FILES (Render / PaaS — no Nginx)
# -----------------------------------------------
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

# HTTPS CSRF (required for login on Render)
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)

# -----------------------------------------------
# DATABASE SSL (DigitalOcean managed MySQL)
# -----------------------------------------------
if config('DB_SSL', default=False, cast=bool):
    ssl_options = {}
    ca_path = config('DB_SSL_CA', default='')
    if ca_path:
        ssl_options['ca'] = ca_path
    DATABASES['default']['OPTIONS']['ssl'] = ssl_options

# -----------------------------------------------
# SECURITY ENHANCEMENTS
# -----------------------------------------------
# HTTPS settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000       # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = True

# Content security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# -----------------------------------------------
# CORS (Restrict in production)
# -----------------------------------------------
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='https://yourdomain.com',
    cast=Csv()
)

# -----------------------------------------------
# LOGGING (File-based in production)
# -----------------------------------------------
LOGGING['root']['handlers'] = ['console', 'file']
LOGGING['root']['level'] = 'WARNING'
