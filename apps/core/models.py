# Importamos los módulos base de Django para crear modelos
from django.db import models
# Importamos el settings para poder referirnos al modelo de Usuario
from django.conf import settings

# --- INICIO: Catálogos para Condominio ---

class CatTipoCuenta(models.Model):
    """
    [MAPEO: Tabla 'cat_tipo_cuenta']
    Catálogo para los tipos de cuenta bancaria (ej: Corriente, Ahorro, Vista).
    """
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


# --- INICIO: Modelos Estructura Condominio --- ¡NUEVOS CATÁLOGOS! ---

class CatSegmento(models.Model):
    """
    [MAPEO: Tabla 'cat_segmento']
    Catálogo para segmentar unidades (ej: 'Residencial', 'Comercial').
    """
    id_segmento = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=60)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'cat_segmento'
        verbose_name = 'Catálogo: Segmento de Unidad'
        verbose_name_plural = 'Catálogo: Segmentos de Unidad'

class CatUnidadTipo(models.Model):
    """
    [MAPEO: Tabla 'cat_unidad_tipo']
    Catálogo para tipos de unidad (ej: 'Depto', 'Casa', 'Bodega', 'Estac').
    """
    id_unidad_tipo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=60)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'cat_unidad_tipo'
        verbose_name = 'Catálogo: Tipo de Unidad'
        verbose_name_plural = 'Catálogo: Tipos de Unidad'

class CatViviendaSubtipo(models.Model):
    """
    [MAPEO: Tabla 'cat_vivienda_subtipo']
    Catálogo para subtipos de vivienda (ej: '1D1B', '2D2B', 'Duplex').
    """
    id_viv_subtipo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=60)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'cat_vivienda_subtipo'
        verbose_name = 'Catálogo: Subtipo de Vivienda'
        verbose_name_plural = 'Catálogo: Subtipos de Vivienda'

# --- FIN: Modelos Estructura Condominio ---


# --- INICIO: Modelo Condominio ---

class Condominio(models.Model):
    """
    [MAPEO: Tabla 'condominio']
    Representa un condominio o edificio administrado en la plataforma.
    """
    id_condominio = models.AutoField(primary_key=True)
    
    nombre = models.CharField(
        max_length=120, 
        unique=True,
        db_comment="Nombre oficial y único del condominio"
    )
    
    rut_base = models.IntegerField(
        null=True, blank=True,
        db_comment="RUT del condominio (sin DV)"
    )
    rut_dv = models.CharField(
        max_length=1, 
        null=True, blank=True,
        db_comment="Dígito verificador del RUT"
    )
    
    direccion = models.CharField(max_length=200, null=True, blank=True)
    comuna = models.CharField(max_length=80, null=True, blank=True)
    region = models.CharField(max_length=80, null=True, blank=True)
    
    email_contacto = models.EmailField(max_length=120, null=True, blank=True)
    telefono = models.CharField(max_length=40, null=True, blank=True)

    banco = models.CharField(max_length=80, null=True, blank=True)
    
    id_tipo_cuenta = models.ForeignKey(
        CatTipoCuenta,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_tipo_cuenta',
        verbose_name='Tipo de Cuenta'
    )
    
    num_cuenta = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'condominio'
        verbose_name = 'Condominio'
        verbose_name_plural = 'Condominios'

# --- FIN: Modelo Condominio ---


# --- INICIO: Modelos de Suscripción (SaaS) ---

class CatPlan(models.Model):
    """
    [NUEVA TABLA - SaaS]
    Catálogo de los planes de suscripción pre-definidos (Esencial, Pro, etc.)
    """
    id_plan = models.AutoField(primary_key=True)
    
    codigo = models.CharField(
        max_length=30, 
        unique=True, 
        help_text="Código interno (ej: 'esencial', 'pro', 'planificador')"
    )
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre comercial del plan (ej: 'Plan Profesional')"
    )
    
    precio_base_mensual = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        default=0,
        help_text="Precio mensual del paquete (si es 0, es 'Planificador')"
    )
    
    max_condominios = models.PositiveSmallIntegerField(
        default=1,
        help_text="Número máximo de condominios permitidos en este plan"
    )
    
    max_unidades = models.PositiveSmallIntegerField(
        default=100,
        help_text="Número máximo de unidades (deptos/casas) totales"
    )

    features_json = models.JSONField(
        default=dict,
        help_text="Banderas JSON que definen qué módulos incluye este plan"
    )
    
    es_personalizable = models.BooleanField(
        default=False,
        help_text="Si es True, este plan es el 'Planificador' (cotizable)"
    )

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'cat_plan'
        verbose_name = 'Catálogo: Plan de Suscripción'
        verbose_name_plural = 'Catálogo: Planes de Suscripción'


class Suscripcion(models.Model):
    """
    [NUEVA TABLA - SaaS]
    La suscripción ACTIVA de un Usuario (admin).
    """
    id_suscripcion = models.AutoField(primary_key=True)

    id_usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        db_column='id_usuario',
        help_text="El usuario (administrador) dueño de esta suscripción"
    )
    
    id_plan = models.ForeignKey(
        CatPlan,
        on_delete=models.PROTECT,
        db_column='id_plan',
        help_text="El plan base o plantilla seleccionado"
    )
    
    class EstadoSuscripcion(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        PRUEBA = 'prueba', 'En Prueba'
        CANCELADA = 'cancelada', 'Cancelada'
        VENCIDA = 'vencida', 'Vencida'

    estado = models.CharField(
        max_length=20,
        choices=EstadoSuscripcion.choices,
        default=EstadoSuscripcion.PRUEBA,
    )
    fecha_inicio = models.DateField(auto_now_add=True)
    fecha_termino = models.DateField(
        null=True, blank=True,
        help_text="Fecha de fin (para planes de prueba o si se cancela)"
    )
    
    monto_mensual_final = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="El monto final calculado que el cliente paga por mes"
    )
    
    max_condominios = models.PositiveSmallIntegerField(
        default=1,
        help_text="Límite real de condominios para ESTA suscripción"
    )
    
    max_unidades = models.PositiveSmallIntegerField(
        default=100,
        help_text="Límite real de unidades para ESTA suscripción"
    )

    features_json = models.JSONField(
        default=dict,
        help_text="Banderas JSON que definen los módulos de ESTA suscripción"
    )
    
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            return f"Suscripción de {self.id_usuario.email} ({self.estado})"
        except Exception:
            return f"Suscripción ID: {self.id_suscripcion} ({self.estado})"

    class Meta:
        db_table = 'suscripcion'
        verbose_name = 'Suscripción de Usuario'
        verbose_name_plural = 'Suscripciones de Usuario'

# --- FIN: Modelos de Suscripción (SaaS) ---