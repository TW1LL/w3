from django.conf.urls import url
from shop_manager import views

urlpatterns = [
    url(r'products', views.products, name="products"),
    url(r'history', views.history, name="history"),
    url(r'order/(?P<order_id>[0-9]+)', views.order, name="order"),
    url(r'', views.open_orders, name="open_orders"),
]