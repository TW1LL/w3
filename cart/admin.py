from django.contrib import admin
from cart.models import Watch, Part, ShoppingCart

# Register your models here.
admin.site.register(Watch)
admin.site.register(Part)
admin.site.register(ShoppingCart)