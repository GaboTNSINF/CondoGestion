from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('condominio/<int:condominio_id>/gastos/', views.gastos_list_view, name='gastos_list'),
    path('condominio/<int:condominio_id>/gastos/nuevo/', views.gasto_create_view, name='gasto_create'),
    path('condominio/<int:condominio_id>/cierre/', views.cierre_mensual_view, name='cierre_mensual'),
    path('condominio/<int:condominio_id>/cobros/<str:periodo>/', views.cobros_list_view, name='cobros_list'),
    path('condominio/<int:condominio_id>/pagos/', views.pagos_list_view, name='pagos_list'),
    path('condominio/<int:condominio_id>/pagos/nuevo/', views.pago_create_view, name='pago_create'),
]
