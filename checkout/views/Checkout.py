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
        return payment(request, order)
    elif order_status in (Order.STATUS_CHOICES['Ready to Ship'], Order.STATUS_CHOICES['Shipped']):
        return confirmation(request, order)
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
                'pk': user_address.customer,
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
                if current_address is not None:
                    form = UserProfileForm(initial={
                        'first_name': current_address.first_name,
                        'last_name': current_address.last_name,
                        'company_name': current_address.company_name,
                        'street_address1': current_address.street_address1,
                        'street_address2': current_address.street_address2,
                        'city': current_address.city,
                        'state': current_address.state,
                        'zipcode': current_address.zipcode,
                        'country': current_address.country,
                        'phone': current_address.phone,
                        'email': current_address.email
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


def payment(request, order):
    summary = order.purchase_info()
    page_vars = view_vars(request)
    page_vars['summary'] = summary

    if request.POST:
        token = request.POST['stripeToken']
        try:
            charge = stripe.Charge.create(
                amount=int(summary['total']['card']),
                currency="usd",
                source=token,
                description="Order #{}".format(order.id)
            )
            order.finalize()
        except stripe.error.CardError as e:
            # handle the failed card
            pass

        # clear the cart quantity manually - bit of a hack
        page_vars['summary']['qty'] = 0

        page_vars['token'] = token
        return render(request, "checkout/confirmation.html", page_vars)
    else:
        summary['image'] = '/static/cart/images/cross-sect.jpg'
        page_vars['stripe'] = stripe_token()
        return render(request, "checkout/accept-payment.html", page_vars)
        

def confirmation(request, order):
    summary = order.purchase_info()
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
