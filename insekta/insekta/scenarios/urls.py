from django.conf.urls import url

from insekta.scenarios import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^view/(.+)$', views.view, name='view'),
]
