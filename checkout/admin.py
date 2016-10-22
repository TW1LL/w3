from django.contrib import admin
from checkout.models import Order, FinalOrder

admin.site.register(Order)
admin.site.register(FinalOrder)