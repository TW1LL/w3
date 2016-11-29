from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.shortcuts import render

from account.forms import RegistrationForm, AddressForm
from account.models import CustomerProfile
from checkout.models import Order
from cart.views.functions import view_vars


def register(request):
    # Check if submitting form
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create user, then authenticate
            form1 = RegistrationForm.save(form, True)
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password2'])
            if user is not None:
                if user.is_active:
                    # Login
                    login(request, user)
                    pageVars = view_vars(request)
                    return render(request, 'account/account.html', pageVars)
                else:
                    # User not enabled
                    pageVars = view_vars(request)
                    return render(request, 'error/custom.html', {'error': 'User is disabled.'})
            else:
                # Login failed
                pageVars = view_vars(request)
                return render(request, 'error/custom.html', {'error': 'User authentication failed.'})
        else:
            # Form not valid
            pageVars = view_vars(request)
            pageVars['form'] = form
            return render(request, 'account/registration.html', pageVars)
    else:
        # Show registration form
        pageVars = view_vars(request)
        pageVars['form'] = RegistrationForm()
        return render(request, 'account/registration.html', pageVars)


# Account related views
@login_required(login_url='/account/login')
def account(request):
    page_vars = view_vars(request)
    customer_profile, created = CustomerProfile.objects.get_or_create(customer=request.user)

    page_vars['orders'] = Order.objects.filter(customer=request.user).order_by('-id')[:2]
    count = 0
    for order in page_vars['orders']:
        page_vars['orders'][count].image = order.get_items()[0].item.preview_image.url
        page_vars['orders'][count].total = order.total
        page_vars['orders'][count].created = order.date_created
        count += 1
    page_vars['info'] = {}
    try:
        page_vars['info']['address'] = customer_profile.address.format_for_display()
    except AttributeError:
        # address not created yet
        page_vars['info']['address'] = "No address provided"

    page_vars['info']['name'] = customer_profile.get_full_name()
    return render(request, 'account/account.html', page_vars)


@login_required(login_url='/account/login')
def change_info(request):
    page_vars = view_vars(request)
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            shipping_form = form.save()
            shipping_form.user = request.user
            shipping_form.save()

            info = CustomerProfile.objects.get(user=request.user.id)

            page_vars['info'] = {}
            page_vars['info']['address'] = info.get_address.split('\n')
            page_vars['info']['name'] = info.get_full_name()
            return render(request, 'account/account.html', page_vars)
        else:
            page_vars['form'] = form
            return render(request, 'account/info_change.html', page_vars)
    else:
        user_profile = CustomerProfile.objects.get(customer=request.user.id)
        user = user_profile.get_full_name().split(' ')
        try:
            address = user_profile.address
        except AttributeError:
            # no valid address
            address = None

        if address is not None:
            form = AddressForm(
                initial={
                    'first_name': address.first_name,
                    'last_name': address.last_name,
                    'company_name': address.company_name,
                    'street_address1': address.street_address1,
                    'street_address2': address.street_address2,
                    'city': address.city,
                    'state': address.state,
                    'zipcode': address.zipcode,
                    'country': address.country,
                    'phone': address.phone,
                    'email': address.email
                })
        else:
            form = AddressForm(initial={
                'first_name': user[0],
                'last_name': user[1]
            })
        page_vars['form'] = form

    return render(request, 'account/info_change.html', page_vars)
