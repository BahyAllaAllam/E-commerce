import os
from pathlib import Path

from PIL import Image
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

BASE_DIR = Path(__file__).resolve().parent.parent


def change_users_images_name(instance, filename):
    """
    Rename uploaded profile images and remove any old image for this user.
    Safely handles the case where the profile/ directory doesn't exist yet.
    """
    ext = filename.split('.')[-1]
    folder = BASE_DIR / 'media' / 'profile'

    # Guard: directory may not exist on first upload
    if folder.exists():
        for img in os.listdir(folder):
            if str(instance.user) in img:
                try:
                    os.remove(folder / img)
                except FileNotFoundError:
                    pass  # Already gone — that's fine

    return f'profile/{instance.user}.{ext}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to=change_users_images_name,
        default='profile/default.jpg',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
    )

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        """Resize oversized profile images to max 300×300 after saving."""
        super().save(*args, **kwargs)
        try:
            img = Image.open(self.image.path)
            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300))
                img.convert('RGB').save(self.image.path)
        except (FileNotFoundError, OSError):
            pass  # Image may not exist on disk (e.g. in tests)

    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'.strip()
