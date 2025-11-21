# apps/usuarios/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- INICIO: Rutas de Autenticación ---
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- Perfil & 2FA ---
    path('perfil/', views.user_profile_view, name='user_profile'),
    path('perfil/verificar/', views.verify_otp_view, name='verify_otp'),
]
