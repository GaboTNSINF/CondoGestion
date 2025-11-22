from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('avisos/', views.avisos_list_view, name='avisos_list'), # New
    path('soporte/', views.soporte_view, name='soporte'), # New

    path('condominio/<int:condominio_id>/gastos/', views.gastos_list_view, name='gastos_list'),
    path('condominio/<int:condominio_id>/gastos/nuevo/', views.gasto_create_view, name='gasto_create'),
    path('condominio/<int:condominio_id>/cierre/', views.cierre_mensual_view, name='cierre_mensual'),
    path('condominio/<int:condominio_id>/cobros/<str:periodo>/', views.cobros_list_view, name='cobros_list'),
    path('condominio/<int:condominio_id>/pagos/', views.pagos_list_view, name='pagos_list'),
    path('condominio/<int:condominio_id>/pagos/nuevo/', views.pago_create_view, name='pago_create'),
    path('condominio/<int:condominio_id>/trabajadores/', views.trabajadores_list_view, name='trabajadores_list'),
    path('condominio/<int:condominio_id>/trabajadores/nuevo/', views.trabajador_create_view, name='trabajador_create'),
    path('condominio/<int:condominio_id>/remuneraciones/', views.remuneraciones_list_view, name='remuneraciones_list'),
    path('condominio/<int:condominio_id>/remuneraciones/nuevo/', views.remuneracion_create_view, name='remuneracion_create'),

    # AJAX Create Endpoints
    path('api/proveedor/create/', views.proveedor_create_ajax, name='proveedor_create_ajax'),
    path('api/categoria/create/', views.categoria_create_ajax, name='categoria_create_ajax'),
]
