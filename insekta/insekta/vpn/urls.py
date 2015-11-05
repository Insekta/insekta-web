from django.conf.urls import url

from insekta.vpn import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^([a-z0-9]{64})/insekta-vpn.tgz$', views.download_bundle, name='download_bundle'),
]
