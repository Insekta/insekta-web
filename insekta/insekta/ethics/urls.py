from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$', views.view_ethics, name='view'),
    url(r'^arguments$', views.view_arguments, name='arguments'),
]
