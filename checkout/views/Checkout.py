import stripe
from decimal import Decimal
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.template import Context

from account.forms import UserProfileForm
from account.models import CustomerProfile
from cart.models import ShoppingCart
from cart.views.functions import view_vars, send_email, stripe_token
from checkout.models import Order, Shipment


@login_required(login_url='/account/login')
def shipment(request):
    cart = ShoppingCart.objects.get(customer=request.user.id)

    # if there's nothing in their cart, send them back to their cart
    if cart.count_items() < 1:
        return HttpResponseRedirect('/cart')

    user_profile, created = CustomerProfile.objects.get_or_create(customer=request.user)
    try:
        order = Order.objects.get(customer=request.user, cart=cart)
    except Order.DoesNotExist:
        return shipping_create(request, user_profile)

    order_status = order.status()

    if order_status == Order.STATUS_CHOICES['Created']:
        return address(request, user_profile, order)
    elif order_status == Order.STATUS_CHOICES['Addressed']:
        return shipping_method(request, user_profile, order)
    elif order_status == Order.STATUS_CHOICES['Shipping Chosen']:
        return payment(request, user_profile, order)
    elif order_status == [Order.STATUS_CHOICES['Ready to Ship'], Order.STATUS_CHOICES['Shipped']]:
        return confirmation(request, user_profile, order)
    else:
        raise Exception("Unable to handle order status.")


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
        page_vars['summary'] = order.purchase_info()
        return render(request, "checkout/shipping.html", page_vars)

  
def shipping_create(request, user_profile):
        order = create_order(request.user)
        if order is False:
            return HttpResponseRedirect("/account")
        else:
            order = Order.objects.filter(customer=request.user, finalized=False)[0]
            user = user_profile.get_full_name().split(' ')
            if user_profile.address is None:
                form = UserProfileForm(initial={
                    'first_name': user[0],
                    'last_name': user[1]
                })
            else:
                current_address = user_profile.address
                if len(current_address) > 1:
                    form = UserProfileForm(initial={
                        'first_name': current_address.first_name,
                        'last_name': current_address.last_name,
                        'street_address': current_address.street_address,
                        'city': current_address.city,
                        'state': current_address.state,
                        'zipcode': current_address.zipcode
                    })
                else:
                    form = UserProfileForm(initial={
                        'first_name': user[0],
                        'last_name': user[1]
                    })
            page_vars = view_vars(request)
            page_vars['form'] = form
            page_vars['summary'] = order.purchase_info()
            
            return render(request, "checkout/shipping.html", page_vars)

  
def shipping_method(request, user_profile, order):
    page_vars = view_vars(request)
    current_order = Order.objects.get(customer=request.user, finalized=False)
    try:
        new_shipment = Shipment.objects.get(order=current_order)
    except Shipment.DoesNotExist:
        new_shipment = Shipment.objects.create(order=current_order)

    # Customer is POSTing the form
    if request.method == "POST" and request.POST:
        chosen_rates = get_choice_rate_ids(request.POST)

        final_rates = {}
        shipments = new_shipment.get_shipments()

        for item_id in shipments:
            item_shipment = shipments[item_id]
            for rate in item_shipment.rates:
                if rate.id in chosen_rates:
                    final_rates[item_id] = rate
                    break
        new_shipment.save_shipments(final_rates)
        new_shipment.set_total_cost()
        return HttpResponseRedirect('/checkout')
    else:
        new_shipment.create_shipments()
        page_vars['shipping_rates'] = new_shipment.view_rates()
        page_vars['summary'] = order.purchase_info()
        return render(request, 'checkout/shipping-method.html', page_vars)


def get_choice_rate_ids(post):
    chosen_rates = []
    for val in post:
        if 'rate_option' in val:
            chosen_rates.append(post[val])
    return chosen_rates


def payment(request, user_profile, order):
    summary = order.purchase_info()
    if request.POST:
        token = request.POST['stripeToken']
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
        

def confirmation(request, user_profile, order):
    summary = order.purchase_info()
    
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
        valid, final = finalize_order(user_profile, order, token, summary)
        if valid:
            order = Order.objects.filter(customer=user_profile, status__startswith="CRE").update(status="CHEKOUT")
            ShoppingCart.objects.filter(customer=request.user).delete()
            
            email = {
                'subject': 'Order Confirmation for ' + summary['desc'],
                'from': 'wcubedcompany@gmail.com',
                'to': user_profile.user.email,
                }
            text = get_template('email/confirmation_email.txt')
            htmlt = get_template('email/confirmation_email.html')
            final.sub = final.total - Decimal(final.get_shipment()['rate'])
            d = Context({ 'order': final, 'shipping': final.get_shipment()
                
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
    cart = ShoppingCart.objects.get(customer=user.id)

    order = Order.objects.create(customer=user,
                                 cart=cart,
                                 date_created=datetime.now(),
                                 date_modified=datetime.now()
                                 )
    return order


def finalize_order(user_profile, order, payment, info):
    # ship = ezpost.buy(order.shipping_object)

    # get the order
    # modify it so it's finalized and has a finalized time
    # do whatever other shit needs to happen
    return True
