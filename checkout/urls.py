from django.conf.urls import url
from checkout import views

urlpatterns = [
    url(r'address', views.Checkout.address, name="address"),
    url(r'address/change', views.Checkout.address, name="address_change"),
    url(r'', views.Checkout.shipment, name="checkout"),
    ]
