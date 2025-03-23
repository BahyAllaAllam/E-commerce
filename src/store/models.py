from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django_countries.fields import CountryField
from phone_field import PhoneField
from django.core.validators import MinLengthValidator, FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db.models import Prefetch


def change_product_images_name(instance, filename):
    """Helper function to change the name of the product image."""
    ext = filename.split(".")[-1]
    return f'store/{instance.name}_{instance.pk}.{ext}'


class Category(models.Model):
    """Model representing product Categories."""
    name = models.CharField(max_length=50, unique=True)

    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    def __str__(self):
        """Return a string representation of the Category."""
        return self.name

    class Meta:
        """The plural name used in the admin interface for the model."""
        verbose_name_plural = "Categories"
        ordering = ['name']


# handling the most repeated quires
class DiscountManager(models.Manager):
    """Custom manager for Discount model queries."""
    def get_active_discounts(self):
        return self.filter(active=True, expired_date__gte=timezone.now())


class Discount(models.Model):
    """Model representing the discount offers."""
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=4, decimal_places=2)
    active = models.BooleanField(default=False)
    expired_date = models.DateField()
    user = models.ManyToManyField(User, related_name='user_discounts', blank=True)

    objects = DiscountManager()

    def __str__(self):
        """Return a string representation of the discount."""
        return self.name

    def clean(self):
        """Ensure the expired date is in the future."""
        if self.expired_date <= timezone.now().date():
            raise ValidationError('The expiration date must be in the future.')

    class Meta:
        ordering = ['-expired_date']


class ProductManager(models.Manager):
    """Custom manager to handle frequent product queries."""

    def get_all_products_with_related_data(self):
        """Retrieve products with related category and discount using select_related for optimization."""
        return self.select_related('category').prefetch_related(
            Prefetch('discount', queryset=Discount.objects.filter(active=True))
        )

    def get_products_by_discount(self, discount):
        """Retrieve products filtered by an active discount."""
        return self.filter(discount=discount, discount__active=True)

    def get_products_by_category(self, category_id):
        """Retrieve products filtered by category."""
        return self.filter(category_id=category_id)

    def get_products_by_name(self, name):
        """Retrieve products filtered by name."""
        return self.filter(name__icontains=name)


class Product(models.Model):
    """Model representing the products."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500)
    category = models.ForeignKey(Category, related_name='product_category', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    discount = models.ManyToManyField(Discount, related_name='products_discount', blank=True)
    digital = models.BooleanField(default=False)
    image = models.ImageField(upload_to=change_product_images_name, default='store/default.png', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])

    objects = ProductManager()

    def __str__(self):
        """Return a string representation of the product."""
        return self.name

    def get_discounted_price(self):
        """Return the price after discount, if applicable."""
        active_discounts = self.discount.filter(active=True)
        if active_discounts.exists():
            max_discount = max([d.percentage for d in active_discounts])
            return self.price * (1 - max_discount / 100)
        return self.price

    class Meta:
        """The plural name used in the admin interface for the model."""
        verbose_name_plural = "Products"
        ordering = ['name']


class ShippingInfo(models.Model):
    """Model representing shipping details."""
    customer = models.ForeignKey(User, related_name='shipping_infos', on_delete=models.CASCADE)
    country = CountryField(blank_label="(select country)")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.PositiveIntegerField()
    address = models.CharField(max_length=100)
    phone = PhoneField(help_text='Required. Contact phone number', validators=[MinLengthValidator(10)])

    def __str__(self):
        """Return a string representation of the ShippingInfo."""
        return f'{self.customer.username} - {self.country}-{self.city}'

    class Meta:
        ordering = ['country', 'city']


class Order(models.Model):
    """Model representing the orders."""
    customer = models.ForeignKey(User, related_name='customer_orders', on_delete=models.DO_NOTHING)
    shipping_info = models.ForeignKey(ShippingInfo, related_name='order_shipping_info', null=True, on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, editable=False)
    complete = models.BooleanField(default=False)
    shipping_status = models.CharField(max_length=15, choices=[('Delivered', 'Delivered'), ('Pending', 'Pending')], default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """Return a string representation of the orders."""
        return f'Order #{self.id} by {self.customer.username}'

    @property
    def get_total_price_for_order(self):
        """Calculate total price for the order."""
        total_price = sum(item.get_total_price for item in self.orderitem_set.all())
        return total_price

    @property
    def get_total_quantity(self):
        """Calculate total quantity for the order."""
        total_quantity = sum([item.quantity for item in self.orderitem_set.all()])
        return total_quantity

    @property
    def get_cart_total(self):
        """Calculate total cart items"""
        total = sum([item.get_total_price for item in self.orderitem_set.all()])
        return total

    @property
    def get_cart_items(self):
        """Calculate total cart items"""
        total = sum([item.quantity for item in self.orderitem_set.all()])
        return total

    @property
    def shipping(self):
        shipping = False
        orderitems = self.orderitem_set.all()
        for i in orderitems:
            if i.product.digital == False:
                shipping = True
        return shipping

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    """Model representing items within an order."""
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=0)

    def __str__(self):
        """Return a string representation of the orders."""
        return f'{self.quantity} x {self.product.name}'

    @property
    def get_total_price(self):
        """Calculate total price based on products and their quantities."""
        total = self.product.get_discounted_price() * self.quantity
        return total

    class Meta:
        ordering = ['product__name']