"""Users App — Web URL Configuration (template-based views)."""

from django.urls import path
from . import views_web

urlpatterns = [
    path('auth/login/', views_web.login_view, name='login'),
    path('auth/logout/', views_web.logout_view, name='logout'),
    path('auth/profile/', views_web.profile_view, name='profile'),
]
