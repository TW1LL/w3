import stripe, easypost
from decimal import Decimal
from cart.models import ShoppingCart
from checkout.models import Order, FinalOrder
from account.models import UserProfile
from cart.views.functions import view_vars, ezpost, send_email, stripe_token
from django.shortcuts import render
from account.forms import UserProfileForm
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.template.loader import get_template
from django.template import Context


@login_required(login_url='/account/login')
def shipment(request):
    userprof, created = UserProfile.objects.get_or_create(user = request.user)
    order = Order.objects.filter(customer=userprof, status__startswith = "CRE")
    if len(order) > 0:
        order = order[0]
        cart = ShoppingCart.objects.filter(owner = request.user.id)
        if len(cart) < 1: #my fix for my dumb order/cart system (can fix this problem by changing the Order model)
            Order.objects.filter(customer = userprof, status__startswith = "CRE").delete()
            return HttpResponseRedirect('/cart')
        if order.status == "CREATED":
            return shipping(request, userprof, order)
        elif order.status == "CRESHIP":
            return shipping_method(request, userprof, order)
        elif order.status == "CRESHME":
            return payment(request, userprof, order)
        elif order.status == "CREPAID":
            return confirmation(request, userprof, order)
        else:
            return HttpResponseRedirect('/account')
    else:
        return shipping_create(request,userprof)


def shipping(request, userprof, order):
    if request.method == "POST":
        form = UserProfileForm(request.POST)
        if form.is_valid():
            UserProfileForm.save(form)
            userprof = UserProfile.objects.get(user = request.user)
            Order.objects.filter(customer = userprof, status__startswith = "CRE").update(status = "CRESHIP")
            return HttpResponseRedirect('/checkout')
        else:
            pageVars = view_vars(request)
            pageVars['form'] = form
            return render(request, 'checkout/shipping.html', pageVars)
    else:
        user = userprof.get_full_name().split(' ')
        if userprof.address is None:
            form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1] })
        else:
            address = userprof.address.split('\n')
            if len(address) > 1:
                form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1], 'street_address': address[0], 'city': address[1].split(', ')[0], 'state': address[1].split(', ')[1], 'zipcode': address[2]})
            else:
                form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1]})
        pageVars = view_vars(request)
        pageVars['form'] = form
        pageVars['summary'] = order.info()
        return render(request, "checkout/shipping.html", pageVars)

  
def shipping_create(request, userprof):
        order = create_order(request.user)
        if order is False:
            return HttpResponseRedirect("/account")
        else:
            order = Order.objects.filter(customer = userprof, status__startswith = "CRE")[0]
            user = userprof.get_full_name().split(' ')
            if userprof.address is None:
                form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1] })
            else:
                address = userprof.address.split('\n')
                if len(address) > 1:
                    form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1],
                                                       'street_address': address[0], 'city': address[1].split(', ')[0],
                                                       'state': address[1].split(', ')[1], 'zipcode': address[2]})
                else:
                    form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1]})
            page_vars = view_vars(request)
            page_vars['form'] = form
            page_vars['summary'] = order.info()
            
            return render(request, "checkout/shipping.html", page_vars)

  
def shipping_method(request, userprof, order):
    pageVars = view_vars(request)
    print(request.POST)
    if request.method == "POST" and 'method' in request.POST:
        rates = ezpost.view_rates()
        for i in rates:
            if i.id == request.POST['method']:
                rate = i
        order = Order.objects.filter(customer=userprof, status__startswith="CRE").update(shipping_object = rate,
                                                                                         status = "CRESHME")
        return HttpResponseRedirect('/checkout')
    else:
        ezpost.create_shipment(order.address())
        pageVars['methods'] = ezpost.view_rates()
        pageVars['summary'] = order.info()
        return render(request, 'checkout/shipping-method.html', pageVars)


def payment(request, userprof, order):
    summary = order.info()
    if request.POST:
        token = request.POST['stripeToken']
        Order.objects.filter(customer=userprof, status__startswith="CRE").update(status="CREPAID", payment=token)
        page_vars = view_vars(request)
        page_vars['summary'] = summary
        page_vars['token'] = token
        return render(request, "checkout/confirmation.html", page_vars)
    else:
        page_vars = view_vars(request)
        summary['image'] = '/static/cart/images/cross-sect.jpg'
        page_vars['stripe'] = stripe_token()
        page_vars['summary'] = summary
        return render(request, "checkout/accept-payment.html", page_vars)
        

def confirmation(request, userprof, order):
    summary = order.info()
    
    if request.POST:
        
        token = request.POST['stripeToken']
        try:
           charge = stripe.Charge.create(
                amount=int(summary['total']['card']),  # amount in cents, again
                currency="usd",
                source=token,
                description=summary['desc']
            )
        except stripe.error.CardError as e:
            return HttpResponseRedirect('/checkout')
        valid, final = finalize_order(userprof, order, token, summary)
        if valid:
            order = Order.objects.filter(customer=userprof, status__startswith="CRE").update(status="CHEKOUT")
            ShoppingCart.objects.filter(owner=request.user).delete()
            
            email = {
                'subject': 'Order Confirmation for ' + summary['desc'],
                'from': 'wcubedcompany@gmail.com',
                'to': userprof.user.email,
                }
            text = get_template('email/confirmation_email.txt')
            htmlt = get_template('email/confirmation_email.html')
            final.sub = final.total - Decimal(final.shipping()['rate'])
            d = Context({ 'order': final, 'shipping': final.shipping()
                
                })
            email['text'] = text.render(d)
            email['html'] = htmlt.render(d)

            send_email(email)
            return HttpResponseRedirect("/order")
    else:
        page_vars = view_vars(request)
        page_vars['summary'] = summary
        page_vars['token'] = order.payment
        return render(request, "checkout/confirmation.html", page_vars)


def create_order(user):
    cart = ShoppingCart.objects.filter(owner = user.id)
    if len(cart) < 1:
        return False
    customer = UserProfile.objects.get(user = user)
    
    order = Order.objects.create(customer = customer)
    for item in cart:
        order.cart.add(item)
    return order


def finalize_order(userprof, order, payment, info):
    ship = ezpost.buy(order.shipping_object)
    final = FinalOrder.objects.create(
        created=timezone.now(),
        modified=timezone.now(),
        customer=userprof,
        status="CHEKOUT",
        desc=info['desc'],
        paymen=payment,
        total=info['total']['total'],
        shipping_address=info['address'],
        shipping_object=order.shipping_object,
        shipping_label=ship[0],
        shipping_tracking=ship[1])
    for product in order.items():
        final.items.add(product.item)
    return True, final


def create_shipment(address):

    return easypost.S
