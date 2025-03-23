from django.urls import path, include
from . import views
from .api_views import ProfileViewSet

app_name = 'users'

urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path('profile/<str:username>/delete', views.delete_user, name='delete-user'),
    path('api/', ProfileViewSet.as_view({'get': 'list'}), name='rest_profile-list'),
    path('api/profile/<str:username>/',
         ProfileViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}),
         name='rest_profile-detail'),
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
]