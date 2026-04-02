from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .models import Profile


@receiver(user_signed_up)
def create_profile_on_signup(sender, request, user, **kwargs):
    """
    Create a Profile for every new user who signs up via allauth.
    Profile.objects.create() already calls save() — no need for a second signal.
    """
    Profile.objects.get_or_create(user=user)
