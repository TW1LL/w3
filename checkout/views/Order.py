from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.templatetags.staticfiles import static

from cart.views.functions import view_vars
from checkout.models import Order


@login_required(login_url='/account/login')
def view(request, order_id=None):
    page_vars = view_vars(request)
    if order_id is None:
        order = Order.objects.filter(customer=request.user).order_by('-id')[0]
        page_vars['title'] = "Latest Order's Summary"
    else:
        page_vars['title'] = "Order Summary"
        order = Order.objects.get(id=order_id)
    page_vars['summary'] = order.purchase_info()
    page_vars['shipment'] = order.shipping_info()
    return render(request, "order/viewOrder.html", page_vars)


@login_required(login_url='/account/login')
def history(request):
    page_vars = view_vars(request)
    order = Order.objects.filter(customer=request.user, finalized=True).order_by('-id')
    page_vars['orders'] = order
    count = 0
    for order in page_vars['orders']:
        try:
            page_vars['orders'][count].image =  order.get_items()[0].item.preview_image.url
        except ValueError:
            page_vars['orders'][count].image =  static('cart/images/w3.png')
        page_vars['orders'][count].total = order.total
        page_vars['orders'][count].created = order.date_created
        count += 1
    return render(request, "order/viewHistory.html", page_vars)
