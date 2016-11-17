from cart.models import Category
from cart.views.functions import view_vars
from django.shortcuts import render
from django.apps import apps


#Product related views
def product(request, model_name=None, product_id=None):

    page_vars = view_vars(request)

    if model_name is None:
        models = Category.get_categories()
        page_vars['categories'] = models
        return render(request, 'cart/categories.html', page_vars)
    elif product_id is None:
        model = apps.get_model('cart', model_name)
        page_vars['products'] = model.objects.all()
        page_vars['category'] = model_name
        return render(request, 'cart/products.html', page_vars)
    else:
        model = apps.get_model('cart', model_name)
        page_vars['product'] = model.objects.get(pk=product_id)
        page_vars['category'] = model_name

        # todo: get parts and images using a model.objects.get
        try:
            page_vars['parts'] = page_vars['product'].parts.all()
        except AttributeError:
            page_vars['parts'] = None

        try:
            page_vars['images'] = page_vars['product'].images.all()
        except AttributeError:
            page_vars['images'] = None

        return render(request, 'cart/product.html', page_vars)

