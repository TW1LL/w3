from django.contrib import admin
from checkout.models import Order, Address, Shipment, Payment

admin.site.register(Order)
admin.site.register(Address)
admin.site.register(Shipment)
admin.site.register(Payment)