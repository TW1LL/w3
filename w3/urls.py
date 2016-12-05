from django.conf.urls import include, url
from django.contrib import admin
from account.views import account
from checkout.views import Order
from django.conf.urls.static import static
from w3 import settings

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^manage/', include('shop_manager.urls')),
    url(r'^account/', include('account.urls')),
    url(r'^accounts/profile', account),
    url(r'^checkout/', include('checkout.urls')),
    url(r'^order$', Order.view),
    url(r'order/history', Order.history),
    url(r'^order/(?P<order_id>[0-9]+)', Order.view),
    url(r'', include('cart.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)