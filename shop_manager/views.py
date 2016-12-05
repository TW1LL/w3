from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test

from checkout.models import Order
from cart.models import Category


def admin_check(user):
    return user.is_superuser


@user_passes_test(admin_check)
def open_orders(request):
    context = {"orders": Order.objects.filter(finalized=True, shipped=False)}

    return render(request, 'orders.html', context)


@user_passes_test(admin_check)
def products(request):
    return render(request, 'products.html')


@user_passes_test(admin_check)
def history(request):
    context = {"orders": Order.objects.filter(finalized=True, shipped=True)}

    return render(request, 'orders.html', context)


@user_passes_test(admin_check)
def order(request, order_id):
    context = {}
    context['title'] = "Order Summary"
    order = Order.objects.get(id=order_id)
    context['summary'] = order.purchase_info()
    context['shipment'] = order.shipping_info()

    return render(request, 'order.html', context)
