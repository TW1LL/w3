from django.shortcuts import render
from cart.views.functions import viewVars
from cart.models import Watch

def index(request):
    pageVars = viewVars(request)
    pageVars['products'] = Watch.objects.all()[:2]
    return render(request, 'page/index.html', pageVars)
    
def about(request):
    pageVars = viewVars(request)
    return render(request, 'page/about.html', pageVars)
    
def contact(request):
    pageVars = viewVars(request)
    return render(request, 'page/contact.html', pageVars)