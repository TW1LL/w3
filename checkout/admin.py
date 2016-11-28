from django.contrib import admin
from checkout.models import Order, Address, Shipment

admin.site.register(Order)
admin.site.register(Address)
admin.site.register(Shipment)