# Importamos el módulo 'admin' de Django
from django.contrib import admin
# Importamos los modelos que hemos creado en 'core'
from .models import (
    CatTipoCuenta, Condominio, CatPlan, Suscripcion,
    CatSegmento, CatUnidadTipo, CatViviendaSubtipo,
    Grupo, Unidad,
    CatDocTipo, Proveedor  # <-- ¡NUEVOS!
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


# --- INICIO: Admin para Catálogos Varios ---

@admin.register(CatTipoCuenta)
class CatTipoCuentaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el catálogo de Tipos de Cuenta.
    """
    list_display = ('id_tipo_cuenta', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')
    ordering = ('id_tipo_cuenta',)

@admin.register(CatDocTipo) # <-- ¡NUEVO!
class CatDocTipoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el catálogo de Tipos de Documento.
    """
    list_display = ('id_doc_tipo', 'codigo', 'nombre')
    search_fields = ('codigo', 'nombre')
    ordering = ('id_doc_tipo',)

# --- FIN: Admin para Catálogos Varios ---


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


# --- INICIO: Admin para Estructura Interna ---

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para los Grupos (Torres, Etapas).
    """
    list_display = ('nombre', 'id_condominio', 'tipo')
    search_fields = ('nombre', 'id_condominio__nombre')
    list_filter = ('id_condominio__nombre', 'tipo')
    raw_id_fields = ('id_condominio',)
    ordering = ('id_condominio__nombre', 'nombre')

@admin.register(Unidad)
class UnidadAdmin(admin.ModelAdmin):
    """
    Configuración del admin para las Unidades (Deptos, Bodegas).
    """
    list_display = (
        'codigo', 
        'id_grupo', 
        'id_unidad_tipo', 
        'id_segmento', 
        'coef_prop', 
        'metros2',
        'habitable'
    )
    search_fields = ('codigo', 'id_grupo__nombre', 'id_grupo__id_condominio__nombre')
    list_filter = (
        'id_grupo__id_condominio__nombre', 
        'id_grupo__nombre', 
        'id_unidad_tipo', 
        'id_segmento',
        'habitable'
    )
    raw_id_fields = ('id_grupo', 'id_unidad_tipo', 'id_viv_subtipo', 'id_segmento')
    ordering = ('id_grupo', 'codigo')
    fieldsets = (
        ('Información Principal', {
            'fields': ('id_grupo', 'codigo', 'direccion', 'habitable')
        }),
        ('Clasificación (Catálogos)', {
            'fields': ('id_unidad_tipo', 'id_viv_subtipo', 'id_segmento')
        }),
        ('Datos Económicos (Prorrateo)', {
            'fields': ('coef_prop', 'metros2', 'rol_sii')
        }),
        ('Configuración Anexos', {
            'fields': ('anexo_incluido', 'anexo_cobrable')
        }),
    )

# --- FIN: Admin para Estructura Interna ---


# --- INICIO: Admin para Proveedor --- ¡NUEVO! ---

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Proveedor.
    """
    list_display = ('nombre', 'rut_base', 'rut_dv', 'tipo', 'email', 'telefono')
    search_fields = ('nombre', 'rut_base', 'email')
    list_filter = ('tipo',)
    ordering = ('nombre',)

# --- FIN: Admin para Proveedor ---


# --- INICIO: Admin para CatPlan ---

@admin.register(CatPlan)
class CatPlanAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el Catálogo de Planes SaaS.
    """
    list_display = (
        'nombre', 
        'codigo', 
        'precio_base_mensual', 
        'max_condominios', 
        'max_unidades', 
        'max_grupos',
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
    list_display = (
        'id_usuario', 
        'id_plan', 
        'estado', 
        'monto_mensual_final',
        'max_grupos',
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