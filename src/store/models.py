# import os
from decimal import Decimal
from pathlib import Path

from django.db import models
from django.contrib.auth.models import User
from django_countries.fields import CountryField
from phone_field import PhoneField
from django.core.validators import MinLengthValidator

# from PIL import Image

# from users.models import Profile

BASE_DIR = Path(__file__).resolve().parent.parent


def change_images_name(instance, filename):
    """Helper function to change the name of the image to the product name."""
    ext = filename.split(".")[-1]
    return f'store/{instance.name}.{ext}'


class Category(models.Model):
    """Model representing the Categories."""
    name = models.CharField(max_length=150)

    def __str__(self):
        """Return a string representation of the Category."""
        return self.name

    class Meta:
        """The plural name used in the admin interface for the model."""
        verbose_name_plural = "Categories"


# handling the most repeated quires
# class DiscountManager(models.Manager):
#     def get_active_discounts(self):
#         return self.filter(active=True)


class Discount(models.Model):
    """Model representing the discount of the products."""
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=3, decimal_places=1)
    active = models.BooleanField(default=False)
    expired_date = models.DateField(auto_now=False, auto_now_add=False)

    # objects = DiscountManager()

    def __str__(self):
        """Return a string representation of the discount."""
        return self.name


# class ProductManager(models.Manager):
#     """Custom manager for the products."""
#     def get_products_by_id(self, ids):
#         return self.filter(id__in=ids)
#
#     def get_all_products(self):
#         return self.all()
#
#     def get_all_products_by_category_id(self, category_id):
#         return self.filter(category=category_id)
#
#     def get_products_by_discount(self, discount):
#         return self.filter(discounts=discount)


class Product(models.Model):
    """Model representing the products."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=False, null=False)
    category = models.ForeignKey(Category, related_name='product_category', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    discount = models.ManyToManyField(Discount, related_name='product_discounts', on_delete=models.SET_NULL, null=True,
                                      blank=True)
    image = models.ImageField(upload_to=change_images_name, default='store/default.jpg')

    # objects = ProductManager()

    def save(self, *args, **kwargs):
        """Override the save method to update the price based on applied discounts."""
        # Calculate the discounted price based on applied discounts
        discounted_price = self.calculate_discounted_price()

        # Update the price attribute with the calculated discounted price
        self.price = discounted_price

        super().save(*args, **kwargs)

    def calculate_discounted_price(self):
        """Calculate the discounted price based on applied discounts."""
        discount_percentage = Decimal(0)
        for discount in self.discount.all():
            discount_percentage += discount.percentage
        discount_amount = self.price * (discount_percentage / 100)
        discounted_price = self.price - discount_amount
        return max(Decimal('0.00'), Decimal(discounted_price))

    def __str__(self):
        """Return a string representation of the product."""
        return self.name

    class Meta:
        """The plural name used in the admin interface for the model."""
        verbose_name_plural = "Products"


# class ShippingInfoManager(models.Manager):
#     """Custom manager for the ShippingInfo model."""
#     GET_BY_CUSTOMER_METHOD = 'get_shipping_info_by_customer'
#
#     def get_shipping_info_by_customer(self, customer):
#         """Get shipping information for a given customer."""
#         return self.filter(customer=customer).first()


class ShippingInfo(models.Model):
    """Model representing shipping information."""
    country = CountryField(blank_label="(select country)")
    city = models.CharField(max_length=100)
    zipcode = models.PositiveIntegerField(validators=[MinLengthValidator(5)])
    address = models.CharField(max_length=100)
    phone = PhoneField(help_text='Required. Contact phone number', validators=[MinLengthValidator(10)])

    def __str__(self):
        """Return a string representation of the ShippingInfo."""
        return f'{self.country}-{self.city}'


class Order(models.Model):
    """Model representing the orders."""
    customer = models.ForeignKey(User, related_name='customer_orders', on_delete=models.DO_NOTHING)
    deleted_user_name = models.CharField(max_length=255, blank=True, null=True)
    deleted_user_email = models.EmailField(blank=True, null=True)
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
        """Return a string representation of the orders."""
        if self.deleted_user_name:
            # check if the user is deleted
            return f'Order_number {self.id} made_by{self.deleted_user_name} (Deleted User)'
        else:
            return f'Order_number {self.id} made_by{self.customer}'

    def save(self, *args, **kwargs):
        """
        Override the save method to handle special logic before saving."""
        if self.customer:
            # If the customer is deleted, store their name and email before deleting

            if hasattr(self.customer, 'get_full_name'):
                # Use get_full_name() if available
                self.deleted_user_name = self.customer.get_full_name()
            else:
                # Use username as a fallback if get_full_name() is not available
                self.deleted_user_name = self.customer.username

            self.deleted_user_email = self.customer.email
            # Clear the ForeignKey to prevent errors
            self.customer = None
        super().save(*args, **kwargs)
