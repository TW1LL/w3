import stripe
import easypost
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.template import Context

from account.forms import UserProfileForm
from account.models import UserProfile
from cart.models import ShoppingCart
from cart.views.functions import view_vars, ezpost, send_email, stripe_token
from checkout.models import Order


@login_required(login_url='/account/login')
def shipment(request):
    cart = ShoppingCart.objects.get(owner=request.user.id)

    # if there's nothing in their cart, send them back to their cart
    if cart.count_items() < 1:
        return HttpResponseRedirect('/cart')

    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    try:
        order = Order.objects.get(customer=request.user, cart=cart)
    except Order.DoesNotExist:
        return shipping_create(request, user_profile)

    if order.status() == Order.STATUS_CHOICES['Created']:
        return address(request, user_profile, order)
    elif order.status() == Order.STATUS_CHOICES['Addressed']:
        return shipping_method(request, user_profile, order)
    elif order.status() == Order.STATUS_CHOICES['Shipping Chosen']:
        return payment(request, user_profile, order)
    elif order.status() == Order.STATUS_CHOICES['Ready to Ship']:
        return confirmation(request, user_profile, order)
    else:
        return HttpResponseRedirect('/account')


def address(request, user_profile, order):
    if request.method == "POST":
        form = UserProfileForm(request.POST)

        if form.is_valid():
            # send the user id from the request, rather than letting the user modify it in the HTML
            form.user = request.user.id
            form.save()
            return HttpResponseRedirect('/checkout')

        else:
            page_vars = view_vars(request)
            page_vars['form'] = form
            return render(request, 'checkout/shipping.html', page_vars)
    else:
        user = user_profile.get_full_name().split(' ')
        if user_profile.address is None:
            form = UserProfileForm(initial={'pk': user_profile.pk, 'first_name': user[0], 'last_name': user[1]})
        else:
            user_address = user_profile.address
            form = UserProfileForm(initial={
                'pk': user_address.user,
                'first_name': user_address.first_name,
                'last_name': user_address.last_name,
                'company_name': user_address.company_name,
                'street_address1': user_address.street_address1,
                'street_address2': user_address.street_address2,
                'city': user_address.city,
                'state': user_address.state,
                'zipcode': user_address.zipcode,
                'country': user_address.country,
                'phone': user_address.phone,
                'email': user_address.email
            })

        page_vars = view_vars(request)
        page_vars['form'] = form
        page_vars['summary'] = order.info()
        return render(request, "checkout/shipping.html", page_vars)

  
def shipping_create(request, userprof):
        order = create_order(request.user)
        if order is False:
            return HttpResponseRedirect("/account")
        else:
            order = Order.objects.filter(customer=request.user, status__startswith = "CRE")[0]
            user = userprof.get_full_name().split(' ')
            if userprof.get_address is None:
                form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1] })
            else:
                address = userprof.get_address.split('\n')
                if len(address) > 1:
                    form = UserProfileForm(initial = {
                        'pk': userprof.pk,
                        'first_name': user[0],
                        'last_name': user[1],
                        'street_address': address[0],
                        'city': address[1].split(', ')[0],
                        'state': address[1].split(', ')[1],
                        'zipcode': address[2]
                    })
                else:
                    form = UserProfileForm(initial = { 'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1]})
            page_vars = view_vars(request)
            page_vars['form'] = form
            page_vars['summary'] = order.info()
            
            return render(request, "checkout/shipping.html", page_vars)

  
def shipping_method(request, userprof, order):
    page_vars = view_vars(request)
    if request.method == "POST" and 'method' in request.POST:
        rates = ezpost.view_rates()
        for i in rates:
            if i.id == request.POST['method']:
                rate = i
        Order.objects.filter(customer=userprof).update(shipping_object=rate)
        return HttpResponseRedirect('/checkout')
    else:
        ezpost.create_shipment(order.get_address())
        page_vars['methods'] = ezpost.view_rates()
        page_vars['summary'] = order.info()
        return render(request, 'checkout/shipping-method.html', page_vars)


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
    cart = ShoppingCart.objects.get(owner=user.id)

    order = Order.objects.create(customer=user,
                                 cart=cart,
                                 date_created=datetime.now(),
                                 date_modified=datetime.now()
                                 )
    return order


def finalize_order(userprof, order, payment, info):
    ship = ezpost.buy(order.shipping_object)

    # get the order
    # modify it so it's finalized and has a finalized time
    # do whatever other shit needs to happen
    return True


def create_shipment(address):

    return easypost.S
