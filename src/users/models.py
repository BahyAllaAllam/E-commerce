from django.db import models
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.contrib.auth.models import User

from PIL import Image
# from store.models import Discount

# from pathlib import Path
# import os

# Overwrite the email field in the user model to set the unique value equals to true
User._meta.get_field('email')._unique = True


# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent


def change_users_images_name(instance, filename):
    """Helper function to change the name of the users image."""
    ext = filename.split(".")[-1]
    return f'profile/{instance.user.username}.{ext}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=change_users_images_name, default='profile/default.jpg')

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        """Override the save method to change the image dimensions."""
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        rgb_img = img.convert('RGB')
        if rgb_img.height > 300 or rgb_img.width > 300:
            output_size = (300, 300)
            rgb_img.thumbnail(output_size)
            rgb_img.save(self.image.path)
