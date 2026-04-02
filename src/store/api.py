from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .viewsets import ProductViewSet, OrderViewSet, ShippingInfoViewSet, ReviewViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'shipping-info', ShippingInfoViewSet, basename='shipping-info')
router.register(r'reviews', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
