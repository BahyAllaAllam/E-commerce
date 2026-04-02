from rest_framework import serializers
from .models import Product, Order, OrderItem, ShippingInfo, Review


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'username', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'username', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    discounted_price = serializers.SerializerMethodField()
    reviews = ReviewSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description',
            'category', 'category_name',
            'price', 'discounted_price',
            'digital', 'image',
            'stock', 'rating', 'num_reviews',
            'created_at', 'reviews',
        ]
        read_only_fields = ['id', 'slug', 'rating', 'num_reviews', 'created_at']

    def get_discounted_price(self, obj):
        return str(obj.get_discounted_price())


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price_at_purchase', 'total_price']
        read_only_fields = ['id', 'price_at_purchase', 'total_price']

    def get_total_price(self, obj):
        return str(obj.get_total_price)


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    cart_total = serializers.SerializerMethodField()
    cart_items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'customer', 'shipping_info',
            'complete', 'shipping_status', 'payment_status',
            'shipping_cost', 'transaction_id',
            'created_at', 'updated_at',
            'cart_total', 'cart_items', 'items',
        ]
        read_only_fields = [
            'id', 'customer', 'transaction_id',
            'cart_total', 'cart_items', 'created_at', 'updated_at',
        ]

    def get_cart_total(self, obj):
        return str(obj.get_cart_total)

    def get_cart_items(self, obj):
        return obj.get_cart_items


class ShippingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingInfo
        fields = [
            'id', 'country', 'city', 'state',
            'zipcode', 'address', 'phone', 'is_default',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
