from django.urls import path
from django.contrib.auth import views as auth_views

from insekta.account import views


app_name = 'account'
urlpatterns = [
    path('', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', auth_views.LoginView.as_view(template_name='account/login.html'),
        name='login'),
    path('logout', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
