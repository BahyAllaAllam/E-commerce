from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    CartView,
    CheckoutView,
    UpdateCartView,
    ProcessOrderView,
    AddReviewView,
    ShippingInfoView
)

app_name = "store"

urlpatterns = [
    path('', ProductListView.as_view(), name='store'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('cart/', CartView.as_view(), name='cart'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('update_item/', UpdateCartView.as_view(), name='update_item'),
    path('process_order/', ProcessOrderView.as_view(), name='process_order'),
    path('product/<slug:slug>/review/', AddReviewView.as_view(), name='add_review'),
    path('shipping_info/', ShippingInfoView.as_view(), name='shipping_info'),
]
