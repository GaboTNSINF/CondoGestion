from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('condominio/<int:condominio_id>/gastos/', views.gastos_list_view, name='gastos_list'),
    path('condominio/<int:condominio_id>/gastos/nuevo/', views.gasto_create_view, name='gasto_create'),
]
