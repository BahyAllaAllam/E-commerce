import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from store.models import Product, Order, OrderItem, ShippingInfo, Review, Category
from store.forms import ReviewForm, ShippingInfoForm
import datetime
import paypalrestsdk
from django.conf import settings


class ProductListView(ListView):
    model = Product
    template_name = 'store/store.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.select_related('category').prefetch_related('reviews')
        
        # Filter by category if provided
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add categories to the context
        context['categories'] = Category.objects.values_list('name', 'slug').distinct()
        
        if self.request.user.is_authenticated:
            order, created = Order.objects.get_or_create(customer=self.request.user, complete=False)
            context['cartItems'] = order.get_cart_items
        else:
            context['cartItems'] = 0
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_arg = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['review_form'] = ReviewForm()
        context['reviews'] = self.object.reviews.select_related('user').all()
        if self.request.user.is_authenticated:
            order, created = Order.objects.get_or_create(customer=self.request.user, complete=False)
            context['cartItems'] = order.get_cart_items
        else:
            context['cartItems'] = 0
        return context


class CartView(LoginRequiredMixin, View):
    def get(self, request):
        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        order_items = order.orderitem_set.select_related('product').all()
        context = {
            'order': order,
            'order_items': order_items,
            'cartItems': order.get_cart_items
        }
        return render(request, 'store/cart.html', context)


class CheckoutView(LoginRequiredMixin, View):
    def get(self, request):
        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        order_items = order.orderitem_set.select_related('product').all()
        shipping_info = ShippingInfo.objects.filter(customer=request.user, is_default=True).first()
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

            product = get_object_or_404(Product, id=product_id)
            order, created = Order.objects.get_or_create(customer=request.user, complete=False)
            order_item, created = OrderItem.objects.get_or_create(order=order, product=product)

            if action == 'add':
                if product.stock > order_item.quantity:
                    order_item.quantity += 1
                else:
                    return JsonResponse({'error': 'Not enough stock available'}, status=400)
            elif action == 'remove':
                order_item.quantity -= 1

            if order_item.quantity <= 0:
                order_item.delete()
            else:
                order_item.save()

            return JsonResponse({
                'message': 'Cart updated successfully',
                'cartItems': order.get_cart_items,
                'cartTotal': order.get_cart_total
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except KeyError:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ProcessOrderView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            transaction_id = datetime.datetime.now().timestamp()

            order, created = Order.objects.get_or_create(customer=request.user, complete=False)
            total = float(data['form']['total'])

            if total == order.get_cart_total:
                order.transaction_id = transaction_id
                order.complete = True
                order.save()

                if order.shipping:
                    ShippingInfo.objects.create(
                        customer=request.user,
                        country=data['shipping']['country'],
                        city=data['shipping']['city'],
                        state=data['shipping']['state'],
                        zipcode=data['shipping']['zipcode'],
                        address=data['shipping']['address'],
                        phone=data['shipping']['phone']
                    )

                # Update product stock
                for item in order.orderitem_set.all():
                    product = item.product
                    product.stock -= item.quantity
                    product.save()

                return JsonResponse({
                    'message': 'Order processed successfully',
                    'order_id': order.id
                })
            else:
                return JsonResponse({'error': 'Total amount mismatch'}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except KeyError:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class AddReviewView(LoginRequiredMixin, View):
    def post(self, request, slug):
        try:
            product = get_object_or_404(Product, slug=slug)
            form = ReviewForm(request.POST)
            
            if form.is_valid():
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                
                return JsonResponse({
                    'message': 'Review added successfully',
                    'rating': product.rating,
                    'num_reviews': product.num_reviews
                })
            else:
                return JsonResponse({'error': form.errors}, status=400)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class ShippingInfoView(LoginRequiredMixin, CreateView):
    model = ShippingInfo
    form_class = ShippingInfoForm
    template_name = 'store/shipping_info.html'

    def form_valid(self, form):
        form.instance.customer = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.request.META.get('HTTP_REFERER', '/')


class PayPalPaymentView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            order_id = data['order_id']
            order = get_object_or_404(Order, id=order_id, customer=request.user)

            # Set up PayPal SDK
            paypalrestsdk.configure({
                "mode": settings.PAYPAL_MODE,
                "client_id": settings.PAYPAL_CLIENT_ID,
                "client_secret": settings.PAYPAL_CLIENT_SECRET
            })

            # Create a payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": "http://localhost:8000/store/payment_success/",
                    "cancel_url": "http://localhost:8000/store/payment_cancelled/"
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": f'Order {order.id}',
                            "sku": "item",
                            "price": str(order.get_total_price_for_order()),
                            "currency": "USD",
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(order.get_total_price_for_order()),
                        "currency": "USD"
                    },
                    "description": f'Payment for Order {order.id}'
                }]
            })

            if payment.create():
                return JsonResponse({'payment_id': payment.id, 'approval_url': payment.links[1].href})
            else:
                return JsonResponse({'error': payment.error}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)


class PaymentSuccessView(LoginRequiredMixin, View):
    def get(self, request):
        payment_id = request.GET.get('paymentId')
        payer_id = request.GET.get('PayerID')

        payment = paypalrestsdk.Payment.find(payment_id)
        if payment.execute({"payer_id": payer_id}):
            # Update order payment status
            order = get_object_or_404(Order, id=payment.transactions[0].description.split(' ')[-1])
            order.payment_status = 'Paid'
            order.save()
            return JsonResponse({'message': 'Payment successful', 'order_id': order.id})
        else:
            return JsonResponse({'error': 'Payment execution failed'}, status=400)


class PaymentCancelledView(LoginRequiredMixin, View):
    def get(self, request):
        return JsonResponse({'message': 'Payment was cancelled'})
