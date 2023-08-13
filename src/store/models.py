from django.db import models
from django.contrib.auth.models import User
from phone_field import PhoneField
from users.models import Profile
from PIL import Image
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def image_upload(instance, filename):
    ext = filename.split(".")[-1]
    folder = BASE_DIR / 'media' / 'store'
    img_list = os.listdir(folder)
    for img in img_list:
        if str(instance.name) in img:
            os.remove(folder / img)

    return f'store/{instance.name}.{ext}'

class Category(models.Model):
    name = models.CharField(max_length=150)

    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    def __str__(self):
        return self.name


class Discount(models.Model):
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=3, decimal_places=1)
    active = models.BooleanField(default=False)
    expired_date = models.DateField(auto_now=False, auto_now_add=False)

    def __str__(self):
        return self.name

    @staticmethod
    def filter_discounts_by_active(discount_id):
        try:
            return Discount.objects.filter(active=discount_id)
        except Exception:
            return None


class Product(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=False, null=False)
    category = models.ForeignKey(Category, related_name='product_category', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    discount = models.ForeignKey(Discount, related_name='product_discount', on_delete=models.SET_NULL, null=True)
    image = models.ImageField(upload_to=image_upload, default='store/default.jpg')

    def __str__(self):
        return self.name

    @staticmethod
    def get_products_by_id(ids):
        return Products.objects.filter(id__in=ids)

    @staticmethod
    def get_all_products():
        return Products.objects.all()

    @staticmethod
    def get_all_products_by_categoryid(category_id):
        try:
            return Products.objects.filter(category=category_id)
        except Exception:
            return None



class ShippingInfo(models.Model):
    customer = models.OneToOneField(User, related_name='customer_shipping_info', on_delete=models.DO_NOTHING)
    country = models.CharField(max_length=100)
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