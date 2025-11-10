# Importamos el módulo 'admin' de Django
from django.contrib import admin
# Importamos los modelos que hemos creado en 'core'
from .models import (
    CatTipoCuenta, Condominio, CatPlan, Suscripcion,
    CatSegmento, CatUnidadTipo, CatViviendaSubtipo
)

# --- INICIO: Admin para Catálogos de Unidad ---

@admin.register(CatSegmento)
class CatSegmentoAdmin(admin.ModelAdmin):
    list_display = ('id_segmento', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')

@admin.register(CatUnidadTipo)
class CatUnidadTipoAdmin(admin.ModelAdmin):
    list_display = ('id_unidad_tipo', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')

@admin.register(CatViviendaSubtipo)
class CatViviendaSubtipoAdmin(admin.ModelAdmin):
    list_display = ('id_viv_subtipo', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')

# --- FIN: Admin para Catálogos de Unidad ---


# --- INICIO: Admin para CatTipoCuenta ---

@admin.register(CatTipoCuenta)
class CatTipoCuentaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el catálogo de Tipos de Cuenta.
    """
    list_display = ('id_tipo_cuenta', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')
    ordering = ('id_tipo_cuenta',)

# --- FIN: Admin para CatTipoCuenta ---


# --- INICIO: Admin para Condominio ---

@admin.register(Condominio)
class CondominioAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Condominio.
    """
    list_display = ('id_condominio', 'nombre', 'rut_base', 'email_contacto', 'telefono')
    search_fields = ('nombre', 'rut_base', 'email_contacto')
    list_filter = ('region', 'comuna')
    fieldsets = (
        ('Información Principal', {
            'fields': ('nombre', ('rut_base', 'rut_dv'))
        }),
        ('Ubicación y Contacto', {
            'fields': ('direccion', 'comuna', 'region', 'email_contacto', 'telefono')
        }),
        ('Datos Bancarios', {
            'fields': ('banco', 'id_tipo_cuenta', 'num_cuenta')
        }),
    )
    ordering = ('nombre',)

# --- FIN: Admin para Condominio ---


# --- INICIO: Admin para CatPlan ---

@admin.register(CatPlan)
class CatPlanAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el Catálogo de Planes SaaS.
    """
    # --- ¡CAMBIO APLICADO! ---
    # Añadimos 'max_grupos' a la lista
    list_display = (
        'nombre', 
        'codigo', 
        'precio_base_mensual', 
        'max_condominios', 
        'max_unidades', 
        'max_grupos', # <-- AÑADIDO
        'es_personalizable'
    )
    search_fields = ('nombre', 'codigo')
    list_filter = ('es_personalizable',)
    ordering = ('precio_base_mensual',)

# --- FIN: Admin para CatPlan ---


# --- INICIO: Admin para Suscripcion ---

@admin.register(Suscripcion)
class SuscripcionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para las Suscripciones de los usuarios.
    """
    # --- ¡CAMBIO APLICADO! ---
    # Añadimos 'max_grupos' a la lista
    list_display = (
        'id_usuario', 
        'id_plan', 
        'estado', 
        'monto_mensual_final',
        'max_grupos', # <-- AÑADIDO
        'fecha_termino'
    )
    search_fields = (
        'id_usuario__email', 
        'id_usuario__nombres', 
        'id_plan__nombre'
    )
    list_filter = ('estado', 'id_plan')
    raw_id_fields = ('id_usuario',)
    ordering = ('id_usuario__email',)

# --- FIN: Admin para Suscripcion ---