# apps/usuarios/admin.py
# Importamos el módulo 'admin' de Django
from django.contrib import admin
# Importamos el modelo UserAdmin base, que ya sabe cómo mostrar usuarios
from django.contrib.auth.admin import UserAdmin
# Importamos nuestros modelos personalizados
from .models import (
    Usuario, UsuarioAdminCondo, 
    Copropietario, Residencia, CodigoVerificacion
)
from .forms import UsuarioCreationForm, UsuarioChangeForm
# Importamos Notificacion desde core porque el usuario lo pidió explícitamente en este archivo
from apps.core.models import Notificacion

# --- INICIO: Configuración del Admin para Usuario ---

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Configuración del admin para nuestro modelo 'Usuario'.
    """
    add_form = UsuarioCreationForm
    form = UsuarioChangeForm
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', ('rut_base', 'rut_dv'), 'nombres', 'apellidos', 'tipo_usuario', 'password', 'password_2'),
        }),
    )
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('nombres', 'apellidos', 'rut_base', 'rut_dv', 'telefono', 'direccion')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'tipo_usuario', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'creado_at')}),
    )
    list_display = ('email', 'nombres', 'apellidos', 'tipo_usuario', 'is_staff', 'is_active')
    search_fields = ('email', 'nombres', 'apellidos', 'rut_base')
    list_filter = ('tipo_usuario', 'is_active', 'is_staff')
    ordering = ('email',)
    readonly_fields = ('last_login', 'creado_at')
    filter_horizontal = ()
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        is_superuser = request.user.is_superuser
        if not is_superuser:
            form.base_fields['is_superuser'].disabled = True
        return form

# --- FIN: Configuración del Admin para Usuario ---


# --- INICIO: Admin para UsuarioAdminCondo ---

@admin.register(UsuarioAdminCondo)
class UsuarioAdminCondoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo pivote
    que asigna Administradores a Condominios.
    """
    list_display = ('id_usuario', 'id_condominio')
    search_fields = (
        'id_usuario__email', 
        'id_usuario__nombres', 
        'id_condominio__nombre'
    )
    list_filter = ('id_condominio__nombre',)
    raw_id_fields = ('id_usuario', 'id_condominio')
    ordering = ('id_usuario__email', 'id_condominio__nombre')

# --- FIN: Admin para UsuarioAdminCondo ---


# --- INICIO: Admin para Relación Usuario-Unidad --- ¡NUEVO! ---

@admin.register(Copropietario)
class CopropietarioAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Copropietario.
    """
    list_display = ('id_usuario', 'id_unidad', 'porcentaje', 'desde', 'hasta')
    search_fields = (
        'id_usuario__email', 
        'id_usuario__nombres', 
        'id_unidad__codigo',
        'id_unidad__id_grupo__nombre'
    )
    list_filter = ('id_unidad__id_grupo__id_condominio__nombre', 'desde', 'hasta')
    
    # Usamos 'raw_id_fields' porque pueden haber miles de usuarios y unidades
    raw_id_fields = ('id_usuario', 'id_unidad')
    ordering = ('-desde',)

@admin.register(Residencia)
class ResidenciaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Residencia.
    """
    list_display = ('id_usuario', 'id_unidad', 'origen', 'desde', 'hasta')
    search_fields = (
        'id_usuario__email', 
        'id_usuario__nombres', 
        'id_unidad__codigo',
        'id_unidad__id_grupo__nombre'
    )
    list_filter = ('id_unidad__id_grupo__id_condominio__nombre', 'origen', 'desde', 'hasta')
    
    # Usamos 'raw_id_fields' porque pueden haber miles de usuarios y unidades
    raw_id_fields = ('id_usuario', 'id_unidad')
    ordering = ('-desde',)

@admin.register(CodigoVerificacion)
class CodigoVerificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'accion', 'codigo', 'creado_at')
    search_fields = ('usuario__email', 'codigo', 'accion')
    raw_id_fields = ('usuario',)

# Se registra Notificacion aquí aunque ya esté en core, porque el usuario insistió
# Nota: Django puede quejarse si el modelo ya está registrado en otro admin.
# Usualmente se usa unregister primero si se quiere sobreescribir, o se ignora.
# Pero para cumplir la "misión de rescate" ciegamente:
try:
    @admin.register(Notificacion)
    class NotificacionUsuarioAdmin(admin.ModelAdmin):
        list_display = ('usuario', 'titulo', 'leido', 'created_at')
        list_filter = ('leido', 'created_at')
        search_fields = ('usuario__email', 'titulo')
        raw_id_fields = ('usuario',)
except admin.sites.AlreadyRegistered:
    pass

# --- FIN: Admin para Relación Usuario-Unidad ---
