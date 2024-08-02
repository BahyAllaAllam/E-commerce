from django.contrib import admin
from .models import *
# Register your models here.


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'price', 'complete', 'shipping_status', 'created_at')
    readonly_fields = ('price',)

    def save_model(self, request, obj, form, change):
        """Override save_model to handle ManyToMany relationships."""
        super().save_model(request, obj, form, change)
        form.save_m2m()
        obj.save()


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'percentage', 'active', 'expired_date')


class ShippingInfoAdmin(admin.ModelAdmin):
    list_display = ('country', 'city', 'zipcode', 'address', 'phone')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'order', 'quantity')


admin.site.register(Category)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ShippingInfo, ShippingInfoAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
