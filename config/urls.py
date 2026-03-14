"""
===========================================
Root URL Configuration
===========================================
All API endpoints are versioned under /api/v1/
Template-based views are served from root paths.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # -----------------------------------------------
    # Django Admin (built-in)
    # -----------------------------------------------
    path('admin/', admin.site.urls),

    # -----------------------------------------------
    # Template-based views (server-rendered pages)
    # -----------------------------------------------
    path('', include('apps.users.urls_web')),               # Login, logout, profile
    path('dashboard/', include('apps.reports.urls_web')),    # Dashboard & reports pages
    path('ledger/', include('apps.general_ledger.urls_web')),
    path('receivable/', include('apps.accounts_receivable.urls_web')),
    path('payable/', include('apps.accounts_payable.urls_web')),

    # -----------------------------------------------
    # REST API endpoints (versioned)
    # -----------------------------------------------
    path('api/v1/auth/', include('apps.users.urls_api')),
    path('api/v1/gl/', include('apps.general_ledger.urls_api')),
    path('api/v1/ar/', include('apps.accounts_receivable.urls_api')),
    path('api/v1/ap/', include('apps.accounts_payable.urls_api')),
    path('api/v1/reports/', include('apps.reports.urls_api')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# -----------------------------------------------
# Admin site customization
# -----------------------------------------------
admin.site.site_header = 'School FMS Administration'
admin.site.site_title = 'School FMS Admin'
admin.site.index_title = 'Financial Management System'
