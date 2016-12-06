from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from django.http import HttpResponseRedirect

from checkout.models import Order
from cart.models import Category, Paintball, Watch


def admin_check(user):
    return user.is_superuser


def identify_category(name):
    if name == "Paintball":
        return Paintball
    elif name == "Watch":
        return Watch
    else:
        raise ValueError("Category couldn't be identified, have you updated this logic with your category?")


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
    context = {"category": category_name, }

    if category_name == "Paintball":
        context['items'] = Paintball.objects.all()
    elif category_name == "Watch":
        context['items'] = Watch.objects.all()

    return render(request, 'category.html', context)


@user_passes_test(admin_check)
def new_product(request, category_name):
    category = identify_category(category_name)

    context = {}

    return render(request, 'product.html', context)


@user_passes_test(admin_check)
def product(request, category_name, item):
    category = identify_category(category_name)

    if request.method == "POST":
        item = category.objects.get(id=item)

    context = {
        'item': category.objects.get(id=item)
    }

    return render(request, 'product.html', context)
