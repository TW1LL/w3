from django.contrib.auth.decorators import login_required
from account.models import UserProfile
from django.contrib.auth import authenticate, login
from account.forms import RegistrationForm, UserProfileForm
from checkout.models import FinalOrder
from cart.views.functions import viewVars
from django.shortcuts import render


def register(request):
    # Check if submitting form
    if (request.method == "POST"):
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Create user, then authenticate
            form1 = RegistrationForm.save(form, True)
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password2'])
            if user is not None:
                if user.is_active:
                    # Login
                    login(request, user)
                    pageVars = viewVars(request)
                    return render(request, 'account/account.html', pageVars)
                else:
                    # User not enabled
                    pageVars = viewVars(request)
                    return render(request, 'error/custom.html', {'error': 'User is disabled.'})
            else:
                # Login failed
                pageVars = viewVars(request)
                return render(request, 'error/custom.html', {'error': 'User authentication failed.'})
        else:
            # Form not valid
            pageVars = viewVars(request)
            pageVars['form'] = form
            return render(request, 'account/registration.html', pageVars)
    else:
        # Show registration form
        pageVars = viewVars(request)
        pageVars['form'] = RegistrationForm()
        return render(request, 'account/registration.html', pageVars)


# Account related views
@login_required(login_url='/account/login')
def account(request):
    pageVars = viewVars(request)
    info, created = UserProfile.objects.get_or_create(user=request.user)

    pageVars['orders'] = FinalOrder.objects.filter(customer=info).order_by('-id')[:2]
    order_items = []
    count = 0
    for order in pageVars['orders']:
        pageVars['orders'][count].image = order.items.all()[0].image
        count += 1
    pageVars['info'] = {}
    pageVars['info']['address'] = info.address.split('\n')
    pageVars['info']['name'] = info.get_full_name()
    return render(request, 'account/account.html', pageVars)


@login_required(login_url='/account/login')
def change_info(request):
    pageVars = viewVars(request)
    if (request.method == "POST"):
        form = UserProfileForm(request.POST)
        if form.is_valid():
            UserProfileForm.save(form)
            info = UserProfile.objects.get(user=request.user.id)

            pageVars['info'] = {}
            pageVars['info']['address'] = info.address.split('\n')
            pageVars['info']['name'] = info.get_full_name()
            return render(request, 'account/account.html', pageVars)
        else:
            pageVars['form'] = form
            return render(request, 'account/info_change.html', pageVars)
    else:
        userprof = UserProfile.objects.get(user=request.user.id)
        user = userprof.get_full_name().split(' ')
        address = userprof.address.split('\n')
        if len(address) > 1:
            form = UserProfileForm(
                initial={'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1], 'street_address': address[0],
                         'city': address[1].split(', ')[0], 'state': address[1].split(', ')[1], 'zipcode': address[2]})
        else:
            form = UserProfileForm(initial={'pk': userprof.pk, 'first_name': user[0], 'last_name': user[1]})
        pageVars['form'] = form

    return render(request, 'account/info_change.html', pageVars)
