# Importamos el módulo 'admin' de Django
from django.contrib import admin
# Importamos los modelos que hemos creado en 'core'
from .models import (
    CatTipoCuenta, Condominio, CatPlan, Suscripcion,
    CatSegmento, CatUnidadTipo, CatViviendaSubtipo,
    Grupo, Unidad,
    CatDocTipo, Proveedor,
    GastoCategoria, Gasto,
    # --- NUEVOS MODELOS FALTANTES ---
    ParamReglamento, FondoReservaMov, InteresRegla, Auditoria, CondominioAnexoRegla
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

@admin.register(CatDocTipo)
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


# --- INICIO: Admin para Proveedor ---

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


# --- INICIO: Admin de Gastos (Sprint 2) ---

@admin.register(GastoCategoria)
class GastoCategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Gasto)
class GastoAdmin(admin.ModelAdmin):
    """
    Gestión completa de gastos.
    """
    list_display = (
        'id_gasto', 'periodo', 'id_gasto_categ', 
        'total', 'fecha_emision', 'id_proveedor'
    )
    list_filter = ('id_condominio', 'periodo', 'id_gasto_categ')
    search_fields = ('descripcion', 'documento_folio', 'id_proveedor__nombre')
    date_hierarchy = 'fecha_emision'
    
    # Usamos raw_id_fields para claves foráneas con muchos datos
    raw_id_fields = ('id_condominio', 'id_proveedor')

    fieldsets = (
        ('Contexto', {
            'fields': ('id_condominio', 'periodo', 'id_gasto_categ')
        }),
        ('Documento', {
            'fields': ('id_proveedor', 'id_doc_tipo', 'documento_folio', 'fecha_emision', 'fecha_venc')
        }),
        ('Montos', {
            'fields': ('neto', 'iva', 'total')
        }),
        ('Detalle', {
            'fields': ('descripcion', 'evidencia_url')
        }),
    )
    # 'total' es calculado, así que lo mostramos como solo lectura
    readonly_fields = ('total',)

# --- FIN: Admin de Gastos ---


# --- INICIO: Admin Faltantes Críticos (Gap Analysis) ---

@admin.register(ParamReglamento)
class ParamReglamentoAdmin(admin.ModelAdmin):
    list_display = ('id_condominio', 'recargo_fondo_reserva_pct', 'interes_mora_anual_pct', 'dias_gracia')
    search_fields = ('id_condominio__nombre',)
    raw_id_fields = ('id_condominio',)

@admin.register(InteresRegla)
class InteresReglaAdmin(admin.ModelAdmin):
    list_display = ('id_condominio', 'id_segmento', 'tasa_anual_pct', 'vigente_desde')
    list_filter = ('id_condominio',)
    raw_id_fields = ('id_condominio', 'id_segmento')

@admin.register(FondoReservaMov)
class FondoReservaMovAdmin(admin.ModelAdmin):
    list_display = ('id_condominio', 'fecha', 'tipo', 'monto', 'periodo')
    list_filter = ('id_condominio', 'tipo', 'periodo')
    search_fields = ('glosa',)
    raw_id_fields = ('id_condominio',)
    readonly_fields = ('fecha',) # Por seguridad, no modificar fecha de movimiento

@admin.register(CondominioAnexoRegla)
class CondominioAnexoReglaAdmin(admin.ModelAdmin):
    list_display = ('id_condominio', 'anexo_tipo', 'id_viv_subtipo', 'vigente_desde')
    list_filter = ('id_condominio', 'anexo_tipo')
    raw_id_fields = ('id_condominio', 'id_viv_subtipo')

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'usuario_email', 'accion', 'entidad', 'entidad_id')
    list_filter = ('accion', 'entidad', 'created_at')
    search_fields = ('usuario_email', 'entidad_id', 'detalle')
    # La auditoría debe ser de solo lectura
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

# --- FIN: Admin Faltantes Críticos ---
