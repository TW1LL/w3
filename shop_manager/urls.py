from django.conf.urls import url
from shop_manager import views

urlpatterns = [
    url(r'categories/(?P<category_name>[a-zA-Z0-9]+)/new', views.new_product, name="new_product"),
    url(r'categories/(?P<category_name>[a-zA-Z0-9]+)/(?P<item_id>[0-9]+)', views.product, name="product"),
    url(r'categories/(?P<category_name>[a-zA-Z0-9]+)', views.category, name="product"),
    url(r'categories', views.categories, name="products"),
    url(r'history', views.history, name="history"),
    url(r'order/(?P<order_id>[0-9]+)', views.order, name="order"),
    url(r'', views.open_orders, name="open_orders"),
]