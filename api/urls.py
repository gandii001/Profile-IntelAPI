from django.urls import path
from .views import ProfileListCreateView, ProfileDetailView, ProfileSearchView


urlpatterns = [
    path('profiles/search', ProfileSearchView.as_view(), name='profile-search'),
    path('profiles/search/', ProfileSearchView.as_view()),
    path('profiles', ProfileListCreateView.as_view(), name='profile-list-create'),
    path('profiles/', ProfileListCreateView.as_view()),
    path('profiles/<uuid:pk>', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/<uuid:pk>/', ProfileDetailView.as_view()),
]