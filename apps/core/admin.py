# Importamos el módulo 'admin' de Django
from django.contrib import admin
# Importamos los modelos que acabamos de crear
from .models import CatTipoCuenta, Condominio

# --- INICIO: Admin para CatTipoCuenta ---

@admin.register(CatTipoCuenta)
class CatTipoCuentaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el catálogo de Tipos de Cuenta.
    """
    # Campos a mostrar en la lista
    list_display = ('id_tipo_cuenta', 'codigo', 'nombre')
    # Campos por los que se puede buscar
    search_fields = ('codigo', 'nombre')
    # Orden por defecto
    ordering = ('id_tipo_cuenta',)

# --- FIN: Admin para CatTipoCuenta ---


# --- INICIO: Admin para Condominio ---

@admin.register(Condominio)
class CondominioAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Condominio.
    """
    # Campos a mostrar en la lista de condominios
    list_display = ('id_condominio', 'nombre', 'rut_base', 'email_contacto', 'telefono')
    
    # Campos por los que se puede buscar
    search_fields = ('nombre', 'rut_base', 'email_contacto')
    
    # Filtros que aparecerán en la barra lateral
    list_filter = ('region', 'comuna')
    
    # Organiza los campos de edición en secciones (fieldsets)
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
    
    # Orden por defecto
    ordering = ('nombre',)

# --- FIN: Admin para Condominio ---