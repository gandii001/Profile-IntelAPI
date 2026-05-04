"""
URL configuration for ProfileService project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from api import auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth endpoints
    path('auth/github', auth_views.github_login, name='github-login'),
    path('auth/github/callback', auth_views.github_callback, name='github-callback'),
    path('auth/refresh', auth_views.refresh_token_view, name='refresh-token'),
    path('auth/logout', auth_views.logout_view, name='logout'),
    
    # API endpoints
    path('api/', include('api.urls')),
    
    # Health check
    path('health', lambda request: Response({'status': 'ok'})),
]