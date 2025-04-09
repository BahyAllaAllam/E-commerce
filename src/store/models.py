from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django_countries.fields import CountryField
from phone_field import PhoneField
from django.core.validators import MinLengthValidator, FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.db.models import Prefetch
from django.utils.text import slugify
from django.core.cache import cache


def change_product_images_name(instance, filename):
    """Helper function to change the name of the product image."""
    ext = filename.split(".")[-1]
    return f'store/{instance.name}_{instance.pk}.{ext}'


class Category(models.Model):
    """Model representing product Categories."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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
        indexes = [
            models.Index(fields=['slug']),
        ]


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
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=500)
    category = models.ForeignKey(Category, related_name='product_category', on_delete=models.SET_NULL, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    discount = models.ManyToManyField(Discount, related_name='products_discount', blank=True)
    digital = models.BooleanField(default=False)
    image = models.ImageField(upload_to=change_product_images_name, default='store/default.png', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])])
    stock = models.PositiveIntegerField(default=0)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    num_reviews = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        # Clear cache when product is updated
        cache.delete_pattern('product_*')

    def __str__(self):
        """Return a string representation of the product."""
        return self.name

    def get_discounted_price(self):
        """Return the price after discount, if applicable."""
        cache_key = f'product_{self.id}_discounted_price'
        discounted_price = cache.get(cache_key)
        
        if discounted_price is None:
            active_discounts = self.discount.filter(active=True)
            if active_discounts.exists():
                max_discount = max([d.percentage for d in active_discounts])
                discounted_price = self.price * (1 - max_discount / 100)
            else:
                discounted_price = self.price
            cache.set(cache_key, discounted_price, 3600)  # Cache for 1 hour
        return discounted_price

    def update_rating(self):
        """Update product rating based on reviews."""
        reviews = self.reviews.all()
        if reviews.exists():
            self.rating = sum(review.rating for review in reviews) / reviews.count()
            self.num_reviews = reviews.count()
            self.save()

    class Meta:
        """The plural name used in the admin interface for the model."""
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]


class Review(models.Model):
    """Model representing product reviews."""
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['product', 'user']),
        ]


class ShippingInfo(models.Model):
    """Model representing shipping details."""
    customer = models.ForeignKey(User, related_name='shipping_infos', on_delete=models.CASCADE)
    country = CountryField(blank_label="(select country)")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.PositiveIntegerField()
    address = models.CharField(max_length=100)
    phone = PhoneField(help_text='Required. Contact phone number', validators=[MinLengthValidator(10)])
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return a string representation of the ShippingInfo."""
        return f'{self.customer.username} - {self.country}-{self.city}'

    class Meta:
        ordering = ['-is_default', 'country', 'city']
        indexes = [
            models.Index(fields=['customer', 'is_default']),
        ]


class Order(models.Model):
    """Model representing the orders."""
    SHIPPING_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    customer = models.ForeignKey(User, related_name='customer_orders', on_delete=models.DO_NOTHING)
    shipping_info = models.ForeignKey(ShippingInfo, related_name='order_shipping_info', null=True, on_delete=models.DO_NOTHING)
    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, editable=False)
    complete = models.BooleanField(default=False)
    shipping_status = models.CharField(max_length=15, choices=SHIPPING_STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    transaction_id = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """Return a string representation of the orders."""
        return f'Order #{self.id} by {self.customer.username}'

    @property
    def get_total_price_for_order(self):
        """Calculate total price for the order including shipping."""
        total_price = sum(item.get_total_price for item in self.orderitem_set.all())
        return total_price + self.shipping_cost

    @property
    def get_total_quantity(self):
        """Calculate total quantity for the order."""
        total_quantity = sum([item.quantity for item in self.orderitem_set.all()])
        return total_quantity

    @property
    def get_cart_total(self):
        """Calculate total cart items including shipping."""
        total = sum([item.get_total_price for item in self.orderitem_set.all()])
        return total + self.shipping_cost

    @property
    def get_cart_items(self):
        """Calculate total cart items."""
        total = sum([item.quantity for item in self.orderitem_set.all()])
        return total

    @property
    def requires_shipping(self):
        """Check if order contains physical items that require shipping."""
        return any(not item.product.digital for item in self.orderitem_set.all())

    @property
    def digital_items(self):
        """Get all digital items in the order."""
        return self.orderitem_set.filter(product__digital=True)

    @property
    def physical_items(self):
        """Get all physical items in the order."""
        return self.orderitem_set.filter(product__digital=False)

    def calculate_shipping_cost(self):
        """Calculate shipping cost based on items and location."""
        if not self.requires_shipping:
            self.shipping_cost = 0
            return

        # Base shipping cost
        base_cost = 5.00  # Example base cost
        
        # Additional cost per physical item
        per_item_cost = 2.00  # Example per item cost
        
        # Calculate total shipping cost
        physical_items_count = self.physical_items.count()
        self.shipping_cost = base_cost + (per_item_cost * physical_items_count)
        
        # Apply location-based adjustments if needed
        if self.shipping_info and self.shipping_info.country:
            # Example: Different shipping rates for different countries
            if self.shipping_info.country.code in ['US', 'CA']:
                self.shipping_cost *= 1.2  # 20% more for US and Canada
            elif self.shipping_info.country.code in ['GB', 'DE', 'FR']:
                self.shipping_cost *= 1.3  # 30% more for European countries

    def save(self, *args, **kwargs):
        if self.requires_shipping and not self.shipping_info:
            raise ValidationError("Shipping information is required for physical items")
        self.calculate_shipping_cost()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['customer', 'created_at']),
            models.Index(fields=['shipping_status']),
            models.Index(fields=['payment_status']),
        ]


class OrderItem(models.Model):
    """Model representing items within an order."""
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=0)
    price_at_purchase = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation of the order item."""
        return f'{self.quantity} x {self.product.name}'

    def save(self, *args, **kwargs):
        if not self.price_at_purchase:
            self.price_at_purchase = self.product.get_discounted_price()
        super().save(*args, **kwargs)

    @property
    def get_total_price(self):
        """Calculate total price based on products and their quantities."""
        return self.price_at_purchase * self.quantity

    class Meta:
        ordering = ['product__name']
        indexes = [
            models.Index(fields=['order', 'product']),
        ]
