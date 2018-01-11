from django.conf.urls import url

from insekta.ethics import views


app_name = 'ethics'
urlpatterns = [
    url(r'^$', views.view_ethics, name='view'),
    url(r'^arguments$', views.view_arguments, name='arguments'),
]
