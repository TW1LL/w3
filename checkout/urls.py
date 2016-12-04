from django.conf.urls import url
from checkout import views

urlpatterns = [
    url(r'address', views.Checkout.address, name="address"),
    url(r'address/change', views.Checkout.address, name="address_change"),
    url(r'confirmation', views.Checkout.confirmation, name="confirmation"),
    url(r'confirmed', views.Checkout.confirmed, name="confirmed"),
    url(r'', views.Checkout.shipment, name="checkout"),
    ]
