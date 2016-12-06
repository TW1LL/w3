from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect

from checkout.models import Order



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
    current_order = Order.objects.get(id=order_id)

    if request.method == "POST":
        current_order.shipped = True
        current_order.save()
        return HttpResponseRedirect("/manage")

    else:
        context = {
            'title': "Order Summary",
            'summary': current_order.purchase_info(),
            'shipment': current_order.shipping_info(),
            'order': current_order
        }

        return render(request, 'order.html', context)
