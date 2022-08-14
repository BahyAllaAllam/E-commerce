from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView
from . import views

app_name = 'users'

urlpatterns = [
    path("register/", views.register, name="register"),
    path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path("profile/", views.profile, name="profile"),
    path('profile/<str:username>/edit/email', views.change_email, name='change_email'),
    path('profile/<str:username>/delete', views.delete_user, name='delete-user'),

]