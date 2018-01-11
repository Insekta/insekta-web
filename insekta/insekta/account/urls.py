from django.conf.urls import url
from django.contrib.auth import views as auth_views

from insekta.account import views


app_name = 'account'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^login$', auth_views.login, name='login', kwargs={
        'template_name': 'account/login.html'
    }),
    url(r'logout$', auth_views.logout, name='logout', kwargs={
        'next_page': '/'
    }),
]
