from django.contrib import admin
from checkout.models import Order, Address

admin.site.register(Order)
admin.site.register(Address)