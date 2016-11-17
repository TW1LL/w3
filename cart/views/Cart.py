from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

from cart.models import ShoppingCart, CartItem, Watch, Paintball
from .functions import view_vars


# Cart Views
@login_required(login_url='/account/login')
def cart_add_product(request, category, product_id):

    # see if the user has a cart already, if not then create one
    try:
        user_cart = ShoppingCart.objects.get(owner=request.user)
    except ShoppingCart.DoesNotExist:
        user_cart = ShoppingCart.objects.create(owner=request.user)

    # get the correct item for the category we're in
    if category == 'watch':
        user_item = Watch.objects.get(id=product_id)
    elif category == 'paintball':
        user_item = Paintball.objects.get(id=product_id)
    else:
        raise KeyError('Product category not found')

    # see if the item already exists in the cart, if so just add 1 to quantity
    # if not, add the item with quantity = 1 to the cart

    cart_items = user_cart.get_cart_items()

    item_in_cart = False
    for cart_item in cart_items:
        if cart_item.item.id == user_item.id:
            item_in_cart = True
            cart_item.change_quantity(1)
            break

    if not item_in_cart:
        CartItem.objects.create(cart=user_cart, item=user_item)

    return HttpResponseRedirect('/cart')


@login_required(login_url='/account/login')
def cart(request):
    page_vars = view_vars(request)
    user_cart = ShoppingCart.objects.get(owner=request.user.id)
    items = user_cart.get_cart_items()
    user_cart.count_items()

    cart_total = 0
    cart_num_items = 0

    for item in items:
        cart_num_items += item.quantity
        cart_total += item.get_price() * item.quantity

    page_vars['total'] = cart_total
    page_vars['item_count'] = cart_num_items
    page_vars['cart'] = items

    return render(request, 'cart/cart.html', page_vars)


@login_required(login_url='/login')
def cart_change_quantity(request, cart_item_id, value):
    cart_item = CartItem.objects.get(id=cart_item_id)

    int_val = int(value)
    cart_item.change_quantity(int_val)

    return HttpResponseRedirect('/cart')
