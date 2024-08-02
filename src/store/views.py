import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from store.models import Product, Order, OrderItem


def store(request):
    # Using prefetch_related to optimize the query
    # active_discounts = Discount.objects.get_active_discounts().prefetch_related('product_discounts')

    cartItems = 0
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        cartItems = order.get_cart_items

    products = Product.objects.all()
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def cart(request):
    order = None
    order_items = []
    cartItems = 0
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        order_items = order.orderitem_set.select_related('product').all()
        cartItems = order.get_cart_items
    context = {'order': order, 'order_items': order_items, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)


def checkout(request):
    order = None
    order_items = []
    cartItems = 0
    shipping = False
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(customer=request.user, complete=False)
        order_items = order.orderitem_set.select_related('product').all()
        cartItems = order.get_cart_items
    context = {'order': order, 'order_items': order_items, 'cartItems': cartItems, 'shipping': shipping}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity = (orderItem.quantity + 1)
    elif action == 'remove':
        orderItem.quantity = (orderItem.quantity - 1)

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)
