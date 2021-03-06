from django.shortcuts import render
from cart.views.functions import view_vars
from cart.models import Watch, Category


def index(request):
    page_vars = view_vars(request)
    page_vars['products'] = Category.objects.all()[:6]
    return render(request, 'page/index.html', page_vars)


def about(request):
    page_vars = view_vars(request)
    return render(request, 'page/about.html', page_vars)


def contact(request):
    page_vars = view_vars(request)
    return render(request, 'page/contact.html', page_vars)