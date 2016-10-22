from django.conf.urls import url
from checkout import views
urlpatterns = [
    url(r'', views.Checkout.shipment, name="checkout")
    ]
