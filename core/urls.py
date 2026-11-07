from django.urls import path

from core import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('buscar/', views.buscar, name='buscar'),
    path('livros/', views.biblioteca, name='biblioteca'),
    path('livros/adicionar/', views.adicionar, name='adicionar'),
    path('livros/<int:pk>/', views.detalhe, name='detalhe'),
    path('livros/<int:pk>/status/', views.alterar_status, name='alterar_status'),
    path('livros/<int:pk>/avaliar/', views.avaliar, name='avaliar'),
    path('livros/<int:pk>/remover/', views.remover, name='remover'),
]
