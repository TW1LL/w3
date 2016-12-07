from django.shortcuts import render, redirect
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect
from django.apps import apps
from django.forms import ModelForm

from checkout.models import Order
from cart.models import Category, Paintball, Watch


def admin_check(user):
    return user.is_superuser


@user_passes_test(admin_check)
def open_orders(request):
    context = {"orders": Order.objects.filter(finalized=True, shipped=False)}

    return render(request, 'orders.html', context)


@user_passes_test(admin_check)
def categories(request):

    context = {
        'categories': Category.get_categories()
    }

    return render(request, 'categories.html', context)


@user_passes_test(admin_check)
def history(request):
    context = {"orders": Order.objects.filter(finalized=True, shipped=True)}

    return render(request, 'orders.html', context)


@user_passes_test(admin_check)
def order(request, order_id):
    current_order = Order.objects.get(id=order_id)

    if request.method == "POST":
        current_order.shipped = True
        current_order.save()
        return HttpResponseRedirect("/manage")

    else:
        context = {
            'title': "Order Summary",
            'summary': current_order.purchase_info(),
            'shipment': current_order.shipping_info(),
            'order': current_order
        }

        return render(request, 'order.html', context)


@user_passes_test(admin_check)
def category(request, category_name):

    item_category = apps.get_model('cart', category_name)

    context = {
        "category": category_name,
        "items": item_category.objects.all()
    }
    return render(request, 'category.html', context)


@user_passes_test(admin_check)
def new_product(request, category_name):

    item_category = apps.get_model('cart', category_name)

    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            item = item_category(
                name=form.cleaned_data['name'],
                description=form.cleaned_data['description'],
                on_hand=form.cleaned_data['on_hand'],
                production_time=form.cleaned_data['production_time'],
                price=form.cleaned_data['price'],
                packaging=form.cleaned_data['packaging'],
                weight=form.cleaned_data['weight'],
                custom_width=form.cleaned_data['custom_width'],
                custom_height=form.cleaned_data['custom_height'],
                custom_depth=form.cleaned_data['custom_depth'],
                preview_image=form.cleaned_data['preview_image'],
                image1=form.cleaned_data['image1'],
                image2=form.cleaned_data['image2'],
                image3=form.cleaned_data['image3'],
                image4=form.cleaned_data['image4'],
                image5=form.cleaned_data['image5']
            )
            item.save()
            return redirect(product, category_name, item.id)
        else:
            new_form = ProductForm(request.POST)
            return render(request, 'product.html', {'form': new_form, 'errors': form.errors})
    else:
        form = ProductForm()
        return render(request, 'product.html', {"category": category_name, 'form': form, 'new': True})


@user_passes_test(admin_check)
def product(request, category_name, item_id):
    item_category = apps.get_model('cart', category_name)
    item = item_category.objects.get(id=item_id)

    form = ProductForm(instance=item)

    context = {
        'form': form,
        "category": category_name
    }

    if request.method == "POST":
        form = ProductForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.save()
            context['form'] = ProductForm(instance=item)
            context['success'] = "Product Updated!"
        else:
            context['form'] = form

    return render(request, 'product.html', context)


class ProductForm(ModelForm):
    class Meta:
        model = Category
        exclude = []
