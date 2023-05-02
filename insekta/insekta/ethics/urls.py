from django.urls import path

from insekta.ethics import views


app_name = 'ethics'
urlpatterns = [
    path('', views.view_ethics, name='view'),
    path('arguments', views.view_arguments, name='arguments'),
]
