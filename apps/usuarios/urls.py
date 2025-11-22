# apps/usuarios/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- INICIO: Rutas de Autenticación ---
    # Usamos CustomLoginView para redirección inteligente basada en roles
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- Perfil & 2FA ---
    # Se usa perfil_update_view para coincidir con la instrucción,
    # aunque internamente la vista se llama user_profile_view en el código original.
    # Sin embargo, vamos a renombrar la vista en views.py para ser consistentes.
    path('perfil/', views.perfil_update_view, name='user_profile'),
    path('perfil/verificar/', views.verify_otp_view, name='verify_otp'),
]
