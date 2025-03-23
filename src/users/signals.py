from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile
from allauth.account.signals import user_signed_up


@receiver(user_signed_up)
def create_profile(sender, request, user, **kwargs):
    Profile.objects.create(user=user)


@receiver(user_signed_up)
def save_profile(sender, user, **kwargs):
    user.profile.save()