from django.conf.urls import url
from django.contrib.auth import views
from account import views as Account
from cart.views.functions import viewVars

urlpatterns = [
        url(r'^$', Account.account, name="account"),
        url(r'^profile/$', Account.account, name='account'),

        url(r'^password/change$', views.password_change, {'template_name': 'account/password_change.html', 'extra_context':viewVars()}, name='password_change'),
        url(r'^password/change/done$', views.password_change_done, {'template_name': 'account/password_change_done.html', 'extra_context':viewVars()}, name='password_change_done'),

        url(r'^register$', Account.register, name='registration'),

        url(r'^password/reset$', views.password_reset, {'template_name': 'account/password_reset.html', 'extra_context':viewVars()}, name='password_reset'),
        url(r'^password/reset/done$', views.password_reset_done, {'template_name': 'account/password_reset_done.html', 'extra_context':viewVars()}, name='password_reset_done'),

        url(r'^change_info$', Account.change_info, name='change_info'),


    url(r'^login$', views.login, {'template_name': 'account/login.html', 'extra_context': viewVars()}),
    url(r'^logout$', views.logout_then_login, {'login_url': '/account/login', 'extra_context': viewVars()}),
]