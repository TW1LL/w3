from cart.models import Product
from cart.views.functions import viewVars
from django.shortcuts import render
from django.apps import apps


#Product related views
def product(request, model_name=None, id=None):

    pageVars = viewVars(request)

    if model_name==None:
        models = Product.subcategories()
        pageVars['categories'] = models
        return render(request, 'cart/categories.html', pageVars)
    elif id==None:
        model = apps.get_model('cart', model_name)
        pageVars['products'] = model.objects.all()
        return render(request, 'cart/products.html', pageVars)
    else:
        model = apps.get_model('cart', model_name)
        pageVars['product'] = model.objects.get(pk=id)
        pageVars['parts'] = pageVars['product'].parts.all()
        return render(request, 'cart/product.html',pageVars)

