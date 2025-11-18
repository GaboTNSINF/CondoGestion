"""
URL configuration for config project.
...
"""
from django.contrib import admin
from django.urls import path, include
# --- IMPORTANTE: Importamos las vistas de nuestra app 'core' ---
from apps.core import views as core_views 

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de autenticación (login, logout)
    path('auth/', include('apps.usuarios.urls')),
    
    # --- NUEVA LÍNEA ---
    # Conectamos la raíz ('') con nuestra vista del dashboard
    path('', core_views.index_view, name='index'),
]