from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum, F
from django.contrib.auth.models import User
from django.utils import timezone
from django_countries.fields import CountryField
from phone_field import PhoneField
from django.core.validators import (
    MinLengthValidator, FileExtensionValidator,
    MinValueValidator, MaxValueValidator,
)
from django.db.models import Prefetch
from django.utils.text import slugify
from django.core.cache import cache


def change_product_images_name(instance, filename):
    """Rename uploaded product images to a consistent format."""
    ext = filename.split('.')[-1]
    return f'store/{instance.name}_{instance.pk}.{ext}'


class Category(models.Model):
    """Product category."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=500, blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [models.Index(fields=['slug'])]


class DiscountManager(models.Manager):
    def get_active_discounts(self):
        return self.filter(active=True, expired_date__gte=timezone.now())


class Discount(models.Model):
    """Percentage-based discount offer."""
    name = models.CharField(max_length=100)
    percentage = models.DecimalField(max_digits=4, decimal_places=2)
    active = models.BooleanField(default=False)
    expired_date = models.DateField()
    user = models.ManyToManyField(User, related_name='user_discounts', blank=True)

    objects = DiscountManager()

    def __str__(self):
        return self.name

    def clean(self):
        if self.expired_date <= timezone.now().date():
            raise ValidationError('The expiration date must be in the future.')

    class Meta:
        ordering = ['-expired_date']


class ProductManager(models.Manager):
    def get_all_products_with_related_data(self):
        return self.select_related('category').prefetch_related(
            Prefetch('discount', queryset=Discount.objects.filter(active=True))
        )

    def get_products_by_discount(self, discount):
        return self.filter(discount=discount, discount__active=True)

    def get_products_by_category(self, category_id):
        return self.filter(category_id=category_id)

    def get_products_by_name(self, name):
        return self.filter(name__icontains=name)


class Product(models.Model):
    """A product available in the store."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(max_length=500)
    category = models.ForeignKey(
        Category, related_name='product_category',
        on_delete=models.SET_NULL, null=True,
    )
    price = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    discount = models.ManyToManyField(Discount, related_name='products_discount', blank=True)
    digital = models.BooleanField(default=False)
    image = models.ImageField(
        upload_to=change_product_images_name,
        default='store/default.png',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
    )
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
        # Only clear this product's cache key, not everything
        cache.delete(f'product_{self.id}_discounted_price')

    def __str__(self):
        return self.name

    def get_discounted_price(self):
        """Return the lowest discounted price, or the base price if no active discount."""
        cache_key = f'product_{self.id}_discounted_price'
        discounted_price = cache.get(cache_key)

        if discounted_price is None:
            active_discounts = self.discount.filter(active=True)
            if active_discounts.exists():
                max_discount = max(d.percentage for d in active_discounts)
                discounted_price = self.price * (1 - max_discount / 100)
            else:
                discounted_price = self.price
            cache.set(cache_key, discounted_price, 3600)

        return discounted_price

    def update_rating(self):
        """Recalculate and persist rating without triggering a full save() cascade."""
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'), count=models.Count('id'))
        Product.objects.filter(pk=self.pk).update(
            rating=result['avg'] or 0,
            num_reviews=result['count'],
        )

    class Meta:
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['price']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]


class Review(models.Model):
    """A user review for a product."""
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_rating()

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']
        indexes = [models.Index(fields=['product', 'user'])]


class ShippingInfo(models.Model):
    """Shipping address for a customer."""
    customer = models.ForeignKey(User, related_name='shipping_infos', on_delete=models.CASCADE)
    country = CountryField(blank_label='(select country)')
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zipcode = models.PositiveIntegerField()
    address = models.CharField(max_length=100)
    phone = PhoneField(
        help_text='Required. Contact phone number',
        validators=[MinLengthValidator(10)],
    )
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.customer.username} - {self.country}-{self.city}'

    class Meta:
        ordering = ['-is_default', 'country', 'city']
        indexes = [models.Index(fields=['customer', 'is_default'])]


class Order(models.Model):
    """A customer order, complete or in-progress (cart)."""
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
    shipping_info = models.ForeignKey(
        ShippingInfo, related_name='order_shipping_info',
        null=True, blank=True, on_delete=models.DO_NOTHING,
    )
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
        return f'Order #{self.id} by {self.customer.username}'

    @property
    def get_cart_total(self):
        """Total item cost + shipping, computed in the DB."""
        result = self.orderitem_set.aggregate(
            total=Sum(F('price_at_purchase') * F('quantity'))
        )
        items_total = result['total'] or Decimal('0.00')
        return items_total + self.shipping_cost

    @property
    def get_total_price_for_order(self):
        """Alias kept for template compatibility."""
        return self.get_cart_total

    @property
    def get_cart_items(self):
        """Total number of items in the cart."""
        result = self.orderitem_set.aggregate(total=Sum('quantity'))
        return result['total'] or 0

    @property
    def get_total_quantity(self):
        return self.get_cart_items

    @property
    def requires_shipping(self):
        return self.orderitem_set.filter(product__digital=False).exists()

    @property
    def digital_items(self):
        return self.orderitem_set.filter(product__digital=True)

    @property
    def physical_items(self):
        return self.orderitem_set.filter(product__digital=False)

    def calculate_shipping_cost(self):
        if not self.requires_shipping:
            self.shipping_cost = Decimal('0.00')
            return

        base_cost = Decimal('5.00')
        per_item_cost = Decimal('2.00')
        physical_count = self.physical_items.count()
        cost = base_cost + (per_item_cost * physical_count)

        if self.shipping_info and self.shipping_info.country:
            country_code = self.shipping_info.country.code
            if country_code in ['US', 'CA']:
                cost *= Decimal('1.2')
            elif country_code in ['GB', 'DE', 'FR']:
                cost *= Decimal('1.3')

        self.shipping_cost = cost

    def save(self, *args, **kwargs):
        if self.pk:  # ← add this guard
            if self.requires_shipping and not self.shipping_info:
                raise ValidationError('Shipping information is required for physical items.')
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
    """A single product line within an order."""
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=0)
    price_at_purchase = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.quantity} x {self.product.name}'

    def save(self, *args, **kwargs):
        if not self.price_at_purchase:
            self.price_at_purchase = self.product.get_discounted_price()
        super().save(*args, **kwargs)

    @property
    def get_total_price(self):
        return self.price_at_purchase * self.quantity

    class Meta:
        ordering = ['product__name']
        indexes = [models.Index(fields=['order', 'product'])]
