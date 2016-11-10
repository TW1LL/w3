from django.conf.urls import url
from cart import views

urlpatterns = [
    # 'Static' pages
    url(r'^$', views.Page.index, name='index'),
    url(r'^about$', views.Page.about, name='about'),
    url(r'^contact$', views.Page.contact, name='contact'),
    
    url(r'^cart$', views.Cart.cart, name='cart'),
    url(r'^cart/qty/(?P<product>[0-9]+)/(?P<value>(\+|-)?\d+)$', views.Cart.cart_change_quantity, name='cart_change_quantity'),
    
    url(r'^product$', views.Product.product, name='product'),
        url(r'^product/(?P<model_name>[a-zA-Z0-9]+)$', views.Product.product, name="categories"),
        url(r'^product/(?P<model_name>[a-zA-Z0-9]+)/(?P<id>[0-9]+)$', views.Product.product, name='product'),
        url(r'^product/(?P<model_name>[a-zA-Z0-9]+)/(?P<id>[0-9]+)/cart$', views.Cart.cart_add_product, name='add to cart'),
]
