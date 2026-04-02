import json
import uuid
from decimal import Decimal, InvalidOperation

import paypalrestsdk
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView, View, CreateView

from store.forms import ReviewForm, ShippingInfoForm
from store.models import Category, Order, OrderItem, Product, ShippingInfo


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_active_order(user):
    """Return (order, created) for the user's current open cart."""
    return Order.objects.get_or_create(
        customer=user,
        complete=False,
        defaults={'transaction_id': str(uuid.uuid4())}
    )

# ---------------------------------------------------------------------------
# Store views
# ---------------------------------------------------------------------------

class ProductListView(ListView):
    model = Product
    template_name = 'store/store.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.select_related('category').prefetch_related('reviews')

        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(description__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.values_list('name', 'slug').distinct()

        if self.request.user.is_authenticated:
            order, _ = get_active_order(self.request.user)
            context['cartItems'] = order.get_cart_items
        else:
            context['cartItems'] = 0
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'  # Fixed: was slug_url_arg (typo)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ReviewForm()
        context['reviews'] = self.object.reviews.select_related('user').all()

        if self.request.user.is_authenticated:
            order, _ = get_active_order(self.request.user)
            context['cartItems'] = order.get_cart_items
        else:
            context['cartItems'] = 0
        return context


class CartView(LoginRequiredMixin, View):
    def get(self, request):
        order, _ = get_active_order(request.user)
        order_items = order.orderitem_set.select_related('product').all()
        context = {
            'order': order,
            'order_items': order_items,
            'cartItems': order.get_cart_items,
        }
        return render(request, 'store/cart.html', context)


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        order, _ = get_active_order(request.user)
        order_items = order.orderitem_set.select_related('product').all()
        shipping_info = ShippingInfo.objects.filter(
            customer=request.user, is_default=True
        ).first()
        context = {
            'order': order,
            'order_items': order_items,
            'cartItems': order.get_cart_items,
            'shipping_info': shipping_info,
        }
        return render(request, 'store/checkout.html', context)


class UpdateCartView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            product_id = data['productId']
            action = data['action']
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid request data'}, status=400)

        product = get_object_or_404(Product, id=product_id)
        order, _ = get_active_order(request.user)
        order_item, _ = OrderItem.objects.get_or_create(order=order, product=product)

        if action == 'add':
            if product.stock <= order_item.quantity:
                return JsonResponse({'error': 'Not enough stock available'}, status=400)
            order_item.quantity += 1
        elif action == 'remove':
            order_item.quantity -= 1
        else:
            return JsonResponse({'error': 'Unknown action'}, status=400)

        if order_item.quantity <= 0:
            order_item.delete()
        else:
            order_item.save()

        return JsonResponse({
            'message': 'Cart updated successfully',
            'cartItems': order.get_cart_items,
            'cartTotal': str(order.get_cart_total),
        })


class ProcessOrderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            client_total = Decimal(str(data['form']['total']))
        except (json.JSONDecodeError, KeyError, InvalidOperation):
            return JsonResponse({'error': 'Invalid request data'}, status=400)

        order, _ = get_active_order(request.user)

        # Security: recalculate server-side and compare using Decimal
        server_total = order.get_cart_total
        if client_total != server_total:
            return JsonResponse({'error': 'Total amount mismatch'}, status=400)

        with transaction.atomic():
            # Use a secure random transaction ID
            order.transaction_id = str(uuid.uuid4())
            order.complete = True
            order.save()
            order.refresh_from_db()

            # Save shipping info if provided and order needs it
            shipping_data = data.get('shipping')
            if order.shipping_info is None and shipping_data:  # Fixed: was order.shipping
                ShippingInfo.objects.create(
                    customer=request.user,
                    country=shipping_data['country'],
                    city=shipping_data['city'],
                    state=shipping_data['state'],
                    zipcode=shipping_data['zipcode'],
                    address=shipping_data['address'],
                    phone=shipping_data['phone'],
                )

            # Bulk-update stock instead of saving one product at a time
            products_to_update = []
            for item in order.orderitem_set.select_related('product').all():
                item.product.stock -= item.quantity
                products_to_update.append(item.product)
            Product.objects.bulk_update(products_to_update, ['stock'])

        return JsonResponse({'message': 'Order processed successfully', 'order_id': order.id})


class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, slug):
        product = get_object_or_404(Product, slug=slug)
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            # Re-fetch updated values after update_rating()
            product.refresh_from_db()
            return JsonResponse({
                'message': 'Review added successfully',
                'rating': str(product.rating),
                'num_reviews': product.num_reviews,
            })
        return JsonResponse({'error': form.errors}, status=400)


class ShippingInfoView(LoginRequiredMixin, CreateView):
    model = ShippingInfo
    form_class = ShippingInfoForm
    template_name = 'store/shipping_info.html'

    def form_valid(self, form):
        form.instance.customer = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', '/')


# ---------------------------------------------------------------------------
# PayPal views
# ---------------------------------------------------------------------------

def _configure_paypal():
    paypalrestsdk.configure({
        'mode': settings.PAYPAL_MODE,
        'client_id': settings.PAYPAL_CLIENT_ID,
        'client_secret': settings.PAYPAL_CLIENT_SECRET,
    })


class PayPalPaymentView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            order_id = data['order_id']
        except (json.JSONDecodeError, KeyError):
            return JsonResponse({'error': 'Invalid request data'}, status=400)

        order = get_object_or_404(Order, id=order_id, customer=request.user)
        _configure_paypal()

        # Use request.build_absolute_uri — no more hardcoded localhost
        return_url = request.build_absolute_uri('/store/payment_success/')
        cancel_url = request.build_absolute_uri('/store/payment_cancelled/')
        total = str(order.get_total_price_for_order)  # property, no ()

        payment = paypalrestsdk.Payment({
            'intent': 'sale',
            'payer': {'payment_method': 'paypal'},
            'redirect_urls': {'return_url': return_url, 'cancel_url': cancel_url},
            'transactions': [{
                'item_list': {
                    'items': [{
                        'name': f'Order {order.id}',
                        'sku': 'item',
                        'price': total,
                        'currency': 'USD',
                        'quantity': 1,
                    }]
                },
                'amount': {'total': total, 'currency': 'USD'},
                'description': f'Payment for Order {order.id}',
            }],
        })

        if payment.create():
            approval_url = next(
                (link.href for link in payment.links if link.rel == 'approval_url'),
                None,
            )
            return JsonResponse({'payment_id': payment.id, 'approval_url': approval_url})
        return JsonResponse({'error': payment.error}, status=400)


class PaymentSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')

        _configure_paypal()
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({'payer_id': payer_id}):
            # Parse order ID safely from description
            try:
                order_id = int(payment.transactions[0].description.split()[-1])
            except (IndexError, ValueError):
                return JsonResponse({'error': 'Could not parse order ID'}, status=400)

            order = get_object_or_404(Order, id=order_id, customer=request.user)
            order.payment_status = 'Paid'
            order.save()
            return JsonResponse({'message': 'Payment successful', 'order_id': order.id})

        return JsonResponse({'error': 'Payment execution failed'}, status=400)


class PaymentCancelledView(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({'message': 'Payment was cancelled'})
