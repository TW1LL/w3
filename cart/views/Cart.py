from django.shortcuts import render
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from cart.models import Watch, ShoppingCart
from .functions import viewVars


# Cart Views
@login_required(login_url='/account/login')
def cart_add_product(request, id):
    if (ShoppingCart.objects.filter(owner=request.user.id, item = id).update(quantity = F('quantity') + 1 ) == 0):
        ShoppingCart.objects.create(owner = request.user, item = Watch.objects.get(pk=id), quantity = 1)
    return HttpResponseRedirect('/cart')

@login_required(login_url='/account/login')
def cart(request):
    pageVars = viewVars(request)
    pageVars['cart'] = ShoppingCart.objects.filter(owner = request.user.id).all()   
    pageVars['total'] = 0
    count = 0
    for item in pageVars['cart']:
        subtotal = item.item.price * item.quantity
        pageVars['cart'][count].subtotal = subtotal
        pageVars['total'] += subtotal
        count += 1
    return render(request, 'cart/cart.html', pageVars)
        
@login_required(login_url='/login')
def cart_change_quantity(request,product,value):
    ShoppingCart.objects.filter(owner = request.user.id, item = product).update(quantity = F('quantity') + value)
    row = ShoppingCart.objects.filter(owner = request.user.id, item = product)
    if(row[0].quantity < 1):
        ShoppingCart.objects.filter(owner = request.user.id, item = product).delete()
    return HttpResponseRedirect('/cart')

