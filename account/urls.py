from django.urls import path

from account import views

app_name = 'account'

urlpatterns = [
    path('', views.login, name='login'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('sair/', views.sair, name='logout'),
    path('perfil/', views.perfil, name='perfil'),
]
