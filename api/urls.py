from django.urls import path
from .views import ProfileListCreateView, ProfileDetailView




urlpatterns = [
    path('profiles', ProfileListCreateView.as_view(), name='profile-list-create'),
    path('profiles/', ProfileListCreateView.as_view()),  # Also accept with slash
    path('profiles/<uuid:pk>', ProfileDetailView.as_view(), name='profile-detail'),
    path('profiles/<uuid:pk>/', ProfileDetailView.as_view()),  # Also accept with slash
]