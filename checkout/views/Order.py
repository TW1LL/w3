from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from cart.views.functions import view_vars
from checkout.models import Order


@login_required(login_url='/account/login')
def view(request, id=None):
    page_vars = view_vars(request)
    if id is None:
        order = Order.objects.filter(customer=request.user).order_by('-id')[0]
        page_vars['title'] = "Latest Order's Summary"
    else:
        page_vars['title'] = "Order Summary"
        order = Order.objects.filter(id=id)[0]
    page_vars['order'] = order
    page_vars['shipment'] = order.get_shipment()
    page_vars['order'].sub = page_vars['order'].total - Decimal(page_vars['shipment']['rate'])
    page_vars['order'].image = order.items.all()[0].image
    return render(request, "order/viewOrder.html", page_vars)


@login_required(login_url='/account/login')
def history(request):
    page_vars = view_vars(request)
    order = Order.objects.filter(customer=request.user).order_by('-id')[:12]
    page_vars['orders'] = order
    count = 0
    for order in page_vars['orders']:
        page_vars['orders'][count].image = order.items.all()[0].image
        count += 1
    return render(request, "order/viewHistory.html", page_vars)
