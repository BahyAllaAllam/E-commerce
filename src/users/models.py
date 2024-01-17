from django.db import models
from PIL import Image
from pathlib import Path
import os
from store.models import Discount

from django.contrib.auth.models import User

# Overwrite the email field in the user model to set the unique value equals to true
User._meta.get_field('email')._unique = True

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def image_upload(instance, filename):
    ext = filename.split(".")[-1]
    folder = BASE_DIR / 'media' / 'profile'
    img_list = os.listdir(folder)
    for img in img_list:
        if str(instance.user) in img:
            os.remove(folder / img)

    return f'profile/{instance.user}.{ext}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=image_upload, default='profile/default.jpg')
    discounts = models.ManyToManyField(Discount, related_name='user_discounts', blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        rgb_img = img.convert('RGB')
        if rgb_img.height > 300 or rgb_img.width > 300:
            output_size = (300, 300)
            rgb_img.thumbnail(output_size)
            rgb_img.save(self.image.path)

    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    @staticmethod
    def get_customer_by_email(email):
        try:
            return Customer.objects.get(email=email)
        except:
            return False