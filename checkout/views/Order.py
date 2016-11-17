from cart.views.functions import view_vars
from django.shortcuts import render
from checkout.models import FinalOrder
from account.models import UserProfile
from django.contrib.auth.decorators import login_required
from decimal import Decimal

@login_required(login_url='/account/login')
def view(request, id=None):
    pageVars = view_vars(request)
    userprof = UserProfile.objects.get(user = request.user)
    if id==None:
        order = FinalOrder.objects.filter(customer = userprof).order_by('-id')[0]
        pageVars['title'] = "Latest Order's Summary"
    else:
        pageVars['title'] = "Order Summary"
        order = FinalOrder.objects.filter(id= id, customer = userprof)[0]
    pageVars['order'] = order
    pageVars['shipment'] = order.shipping()
    pageVars['order'].sub = pageVars['order'].total - Decimal(pageVars['shipment']['rate'])
    pageVars['order'].image = order.items.all()[0].image
    return render(request, "order/viewOrder.html", pageVars)

@login_required(login_url='/account/login')
def history(request):
    pageVars = view_vars(request)
    userprof = UserProfile.objects.get(user = request.user)
    order = FinalOrder.objects.filter(customer = userprof).order_by('-id')[:12]
    pageVars['orders'] = order
    count = 0
    for order in pageVars['orders']:
        pageVars['orders'][count].image = order.items.all()[0].image
        count += 1
    return render(request, "order/viewHistory.html", pageVars)
