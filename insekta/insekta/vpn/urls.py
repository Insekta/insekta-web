from django.urls import path, re_path

from insekta.vpn import views


app_name = 'vpn'
urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^([a-z0-9]{64})/insekta-vpn.ovpn$', views.download_config, name='download_config'),
]
