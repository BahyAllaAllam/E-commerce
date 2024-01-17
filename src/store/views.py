from django.shortcuts import render


def store(request):
    # Using prefetch_related to optimize the query
    # active_discounts = Discount.objects.get_active_discounts().prefetch_related('product_discounts')
    context = {}
    return render(request, 'store/store.html', context)


def cart(request):
    context = {}
    return render(request, 'store/cart.html', context)


def checkout(request):
    context = {}
    return render(request, 'store/checkout.html', context)
