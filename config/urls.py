"""
URL configuration for config project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de autenticación (login, logout)
    path('auth/', include('apps.usuarios.urls')),
    
    # Rutas de la app 'core' (Dashboard, Gastos, etc.)
    # Delegamos el manejo de rutas a apps/core/urls.py
    path('', include('apps.core.urls')),
]
