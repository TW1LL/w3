from django.shortcuts import render
from cart.views.functions import viewVars
from cart.models import Watch


def index(request):
    page_vars = viewVars(request)
    page_vars['products'] = Watch.objects.all()[:2]
    return render(request, 'page/index.html', page_vars)


def about(request):
    page_vars = viewVars(request)
    return render(request, 'page/about.html', page_vars)


def contact(request):
    page_vars = viewVars(request)
    return render(request, 'page/contact.html', page_vars)