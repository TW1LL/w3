from django.core.mail import EmailMultiAlternatives
import easypost
import stripe

from w3 import settings
from cart.models import ShoppingCart

if settings.DEBUG:
    easypost.api_key = 'PtuiK6fa0pnWTL9cVMbT4A'
    stripe.api_key = 'sk_test_rkjc0dbKQXNuxKL8Vv3ufwBl'
else:
    easypost.api_key = '9bu7oUwgGAhvXJbG6IvqPQ'
    stripe.api_key = 'sk_live_Hic99hSOWFmRHzeuCgOiXvIS'


def view_vars(request=None):
    page = {
        'title': 'w3',
        'slogan': '',
        'nav': [{'link': '/', 'title': 'Home'},
                   {'link': '/product', 'title': 'Products'},
                    {'link': '/contact', 'title': 'Contact'}],
        'usernav': {
            'dropdown': [{'link': '/account/register', 'title': 'Register'},
                         {'link': '/account/login', 'title': 'Login'}],
            'title': 'Account'
        },
        'user': None
    }

    cart_count = 0

    # Changes navbar items if logged in
    if request is None:
        pass
    else:
        if request.user.is_authenticated():
            page['user'] = request.user
            page['usernav']['title'] = request.user.username
            page['usernav']['dropdown'][0] = {'link': '/account', 'title': 'Account'}
            page['usernav']['dropdown'][1] = {'link': '/account/logout', 'title': 'Logout'}
            try:
                cart = ShoppingCart.objects.get(customer=request.user.id)
            except ShoppingCart.DoesNotExist:
                cart = ShoppingCart.objects.create(customer=request.user)
            cart_count = cart.count_items()
        else:
            cart_count = 0
            page['user'] = None
            page['usernav']['title'] = 'Account'
            page['usernav']['dropdown'][0] = {'link': '/account/register', 'title': 'Register'}
            page['usernav']['dropdown'][1] = {'link': '/account/login', 'title': 'Login'}
        
    return {'page': page, 'cart_count': cart_count }


def send_email(email):
    msg = EmailMultiAlternatives(email['subject'], email['text'], email['from'], [email['to']])
    msg.attach_alternative(email['html'], "text/html")
    msg.send()
