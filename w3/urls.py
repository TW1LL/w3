from django.conf.urls import include, url
from django.contrib import admin
from account import views as Account
from checkout.views import Checkout, Order
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('account.urls')),
    url(r'^accounts/profile', Account.account),
    url(r'^checkout', Checkout.shipment ),
    url(r'^order$', Order.view),
    url(r'order/history', Order.history),
    url(r'^order/(?P<id>[0-9]+)', Order.view),

    url(r'', include('cart.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)