# Importamos los módulos base de Django para crear modelos
from django.db import models

# --- INICIO: Catálogos para Condominio ---

class CatTipoCuenta(models.Model):
    """
    [MAPEO: Tabla 'cat_tipo_cuenta']
    Catálogo para los tipos de cuenta bancaria (ej: Corriente, Ahorro, Vista).
    """
    # id_tipo_cuenta: Django lo crea automáticamente (id)
    id_tipo_cuenta = models.AutoField(primary_key=True)
    
    codigo = models.CharField(
        max_length=20, 
        unique=True,
        db_comment="Código único para el tipo de cuenta, ej: 'CTA_CTE', 'AHORRO'"
    )
    
    # Añadimos un campo 'nombre' para que sea más descriptivo en el admin
    nombre = models.CharField(
        max_length=60,
        db_comment="Nombre descriptivo, ej: 'Cuenta Corriente'"
    )

    def __str__(self):
        """Representación en texto del modelo"""
        return self.nombre # Mostramos el nombre, es más amigable

    class Meta:
        db_table = 'cat_tipo_cuenta'
        verbose_name = 'Catálogo: Tipo de Cuenta Bancaria'
        verbose_name_plural = 'Catálogo: Tipos de Cuenta Bancaria'

# --- FIN: Catálogos para Condominio ---


# --- INICIO: Modelo Condominio ---

class Condominio(models.Model):
    """
    [MAPEO: Tabla 'condominio']
    Representa un condominio o edificio administrado en la plataforma.
    """
    # id_condominio: Django lo crea automáticamente (id)
    id_condominio = models.AutoField(primary_key=True)
    
    nombre = models.CharField(
        max_length=120, 
        unique=True,
        db_comment="Nombre oficial y único del condominio"
    )
    
    # RUT (basado en el SQL)
    rut_base = models.IntegerField(
        null=True, blank=True, # Permitimos nulos como en el SQL
        db_comment="RUT del condominio (sin DV)"
    )
    rut_dv = models.CharField(
        max_length=1, 
        null=True, blank=True,
        db_comment="Dígito verificador del RUT"
    )
    
    # Campos de Ubicación (basado en el SQL)
    direccion = models.CharField(max_length=200, null=True, blank=True)
    comuna = models.CharField(max_length=80, null=True, blank=True)
    region = models.CharField(max_length=80, null=True, blank=True)
    
    # Campos de Contacto (basado en el SQL)
    email_contacto = models.EmailField(max_length=120, null=True, blank=True)
    telefono = models.CharField(max_length=40, null=True, blank=True)

    # --- Campos Bancarios (basado en el SQL) ---
    banco = models.CharField(max_length=80, null=True, blank=True)
    
    # Llave Foránea (FK) a CatTipoCuenta
    # Esto crea la relación con la tabla 'cat_tipo_cuenta'
    id_tipo_cuenta = models.ForeignKey(
        CatTipoCuenta,
        on_delete=models.SET_NULL, # Si se borra un tipo de cuenta, pone NULL aquí
        null=True, blank=True,
        db_column='id_tipo_cuenta', # Nombre exacto de la columna en el SQL
        verbose_name='Tipo de Cuenta'
    )
    
    num_cuenta = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        """Representación en texto del modelo"""
        return self.nombre

    class Meta:
        db_table = 'condominio'
        verbose_name = 'Condominio'
        verbose_name_plural = 'Condominios'
        # El 'uk_condominio_nombre' ya está cubierto por 'unique=True' en el campo 'nombre'

# --- FIN: Modelo Condominio ---