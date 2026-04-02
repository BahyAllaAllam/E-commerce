import uuid
from .models import Order

def cart_items(request):
    cartItems = 0
    if request.user.is_authenticated:
        order, created = Order.objects.get_or_create(
            customer=request.user,
            complete=False,
            defaults={'transaction_id': str(uuid.uuid4())}
        )
        cartItems = order.get_cart_items
    return {'cartItems': cartItems}