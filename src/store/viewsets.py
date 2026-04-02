from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Product, Order, ShippingInfo, Review
from .serializers import (
    ProductSerializer, OrderSerializer,
    ShippingInfoSerializer, ReviewSerializer,
)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only product listing. Write access is admin-only via the admin panel."""
    queryset = Product.objects.select_related('category').prefetch_related('discount', 'reviews')
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category__name']
    ordering_fields = ['price', 'rating', 'created_at']
    lookup_field = 'slug'


class OrderViewSet(viewsets.ModelViewSet):
    """Customers can only see and manage their own orders."""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Order.objects.all().select_related('customer', 'shipping_info')
        return Order.objects.filter(customer=user).select_related('shipping_info')

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class ShippingInfoViewSet(viewsets.ModelViewSet):
    """Customers manage their own shipping addresses."""
    serializer_class = ShippingInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShippingInfo.objects.filter(customer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)


class ReviewViewSet(viewsets.ModelViewSet):
    """Users can read all reviews but only write/edit their own."""
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        return Review.objects.select_related('user', 'product').all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsReviewOwner()]
        return super().get_permissions()


class IsReviewOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
