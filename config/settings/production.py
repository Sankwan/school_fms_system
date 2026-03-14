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
# SECURITY ENHANCEMENTS
# -----------------------------------------------
# HTTPS settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000       # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
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
