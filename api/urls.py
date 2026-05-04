from django.urls import path
from .views import (
    ProfileListCreateView,
    ProfileDetailView,
    ProfileSearchView,
    export_profiles
)
from .auth_views import (
    github_login,
    github_callback,
    refresh_token_view,
    logout_view
)

urlpatterns = [
    # Profile endpoints
    path('profiles', ProfileListCreateView.as_view(), name='profile-list-create'),
    path('profiles/<uuid:profile_id>', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/search', ProfileSearchView.as_view(), name='profile-search'),
    path('profiles/export', export_profiles, name='profile-export'),
]