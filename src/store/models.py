# import os
from pathlib import Path

from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from phone_field import PhoneField

# from PIL import Image

# from users.models import Profile

BASE_DIR = Path(__file__).resolve().parent.parent


def image_upload(instance, filename):
    ext = filename.split(".")[-1]
    return f'store/{instance.name}.{ext}'


class Category(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


# handling the most repeated quires
class DiscountManager(models.Manager):
    def get_active_discounts(self):
        return self.filter(active=True)


class Discount(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=3, decimal_places=1)
    active = models.BooleanField(default=False)
    expired_date = models.DateField(auto_now=False, auto_now_add=False)

    objects = DiscountManager()

    def __str__(self):
        return self.name


class ProductManager(models.Manager):
    def get_products_by_id(self, ids):
        return self.filter(id__in=ids)

    def get_all_products(self):
        return self.all()

    def get_all_products_by_category_id(self, category_id):
        return self.filter(category=category_id)

    def get_products_by_discount(self, discount):
        return self.filter(discounts=discount)


class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=False, null=False)
    category = models.ForeignKey(Category, related_name='product_category', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    discount = models.ManyToManyField(Discount, related_name='product_discounts', on_delete=models.SET_NULL, null=True,
                                      blank=True)
    image = models.ImageField(upload_to=image_upload, default='store/default.jpg')

    objects = ProductManager()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Products"


class ShippingInfo(models.Model):
    customer = models.OneToOneField(User, related_name='customer_shipping_info', on_delete=models.DO_NOTHING)
    country = CountryField(blank_label="(select country)")
    city = models.CharField(max_length=100)
    zipcode = models.PositiveIntegerField()
    address = models.CharField(max_length=100)
    phone = PhoneField(help_text='Required. Contact phone number')

    def __str__(self):
        return f'{self.customer}_shipping_info'

    @staticmethod
    def get_ShippingInfo_by_customer(customer_id):
        try:
            return ShippingInfo.objects.filter(customer=customer_id)
        except Exception:
            return None


class Order(models.Model):
    products = models.ManyToManyField(Product, related_name='products_order')
    shipping_info = models.ForeignKey(ShippingInfo, related_name='order_shipping_info', on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    payment_status = models.CharField(max_length=15, choices=[('Paid', 'Paid'), ('Not paid', 'Not paid')])
    complete = models.BooleanField(default=False)
    shipping_satus = models.CharField(max_length=15, choices=[('Delivered', 'Delivered'), ('Pending', 'Pending')])
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    modified_at = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return f'Order_{self.id}_made_by{self.shipping_info.customer}'

    @staticmethod
    def get_orders_by_customer(customer_id):
        return Order.objects.filter(customer=customer_id).order_by('-date')
