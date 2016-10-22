from cart.models import Watch
from cart.views.functions import viewVars
from django.shortcuts import render


#Product related views
def product(request, id=None):
    pageVars = viewVars(request)
    if id==None:
        pageVars['products'] = Watch.objects.all()
        return render(request, 'cart/products.html',pageVars)
    else:
        pageVars['product'] = Watch.objects.get(pk=id)
        pageVars['parts'] = pageVars['product'].parts.all()
        return render(request, 'cart/product.html',pageVars)

