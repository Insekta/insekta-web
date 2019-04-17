from django.conf.urls import url
from django.contrib.auth import views as auth_views

from insekta.account import views


app_name = 'account'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^register$', views.register, name='register'),
    url(r'^login$', auth_views.LoginView.as_view(template_name='account/login.html'),
        name='login'),
    url(r'logout$', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
