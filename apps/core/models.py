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


# --- INICIO: Catálogos de Estructura Condominio ---

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

# --- FIN: Catálogos de Estructura Condominio ---


# --- INICIO: Catálogos de Gastos y Pagos --- ¡NUEVO! ---

class CatDocTipo(models.Model):
    """
    [MAPEO: Tabla 'cat_doc_tipo']
    Catálogo para tipos de documentos (ej: 'Factura', 'Boleta', 'Recibo').
    """
    id_doc_tipo = models.AutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    # Añadimos un 'nombre' para que sea más descriptivo
    nombre = models.CharField(max_length=60, default='')

    def __str__(self):
        return self.nombre or self.codigo
    class Meta:
        db_table = 'cat_doc_tipo'
        verbose_name = 'Catálogo: Tipo de Documento'
        verbose_name_plural = 'Catálogo: Tipos de Documento'

# --- FIN: Catálogos de Gastos y Pagos ---


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


# --- INICIO: Modelos de Estructura Interna ---

class Grupo(models.Model):
    """
    [MAPEO: Tabla 'grupo']
    Representa un agrupador lógico dentro de un condominio (Torre, Etapa).
    """
    id_grupo = models.AutoField(primary_key=True)
    id_condominio = models.ForeignKey(
        Condominio,
        on_delete=models.RESTRICT,
        db_column='id_condominio'
    )
    nombre = models.CharField(max_length=80)
    tipo = models.CharField(
        max_length=45,
        db_comment="Tipo de grupo, ej: 'Torre', 'Etapa', 'Sector'"
    )

    def __str__(self):
        try:
            return f"{self.nombre} ({self.id_condominio.nombre})"
        except Exception:
            return f"Grupo ID: {self.id_grupo}"
    class Meta:
        db_table = 'grupo'
        unique_together = ('id_condominio', 'nombre')
        verbose_name = 'Grupo (Torre/Etapa)'
        verbose_name_plural = 'Grupos (Torres/Etapas)'

class Unidad(models.Model):
    """
    [MAPEO: Tabla 'unidad']
    Representa una unidad individual (Depto, Casa, Bodega).
    """
    id_unidad = models.AutoField(primary_key=True)
    id_grupo = models.ForeignKey(
        Grupo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_grupo',
        verbose_name='Grupo (Torre/Etapa)'
    )
    codigo = models.CharField(
        max_length=40,
        db_comment="Código/Nro de la unidad, ej: 'DEPTO-101', 'BOD-01', 'EST-12'"
    )
    direccion = models.CharField(max_length=200, null=True, blank=True)
    id_unidad_tipo = models.ForeignKey(
        CatUnidadTipo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_unidad_tipo',
        verbose_name='Tipo de Unidad'
    )
    id_viv_subtipo = models.ForeignKey(
        CatViviendaSubtipo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_viv_subtipo',
        verbose_name='Subtipo de Vivienda'
    )
    id_segmento = models.ForeignKey(
        CatSegmento,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_segmento',
        verbose_name='Segmento'
    )
    anexo_incluido = models.BooleanField(default=False)
    anexo_cobrable = models.BooleanField(default=False)
    rol_sii = models.CharField(max_length=40, null=True, blank=True)
    metros2 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    coef_prop = models.DecimalField(
        max_digits=8, 
        decimal_places=6,
        db_comment="Coeficiente de propiedad (alícuota)"
    )
    habitable = models.BooleanField(default=True)

    def __str__(self):
        try:
            return f"Unidad {self.codigo} (Grupo: {self.id_grupo.nombre if self.id_grupo else 'N/A'})"
        except Exception:
            return f"Unidad ID: {self.id_unidad}"
    class Meta:
        db_table = 'unidad'
        unique_together = ('id_grupo', 'codigo')
        verbose_name = 'Unidad (Depto/Casa)'
        verbose_name_plural = 'Unidades (Deptos/Casas)'

# --- FIN: Modelos de Estructura Interna ---


# --- INICIO: Modelos de Negocio (Gastos y Pagos) --- ¡NUEVO! ---

class Proveedor(models.Model):
    """
    [MAPEO: Tabla 'proveedor']
    Representa una entidad (persona o empresa) que emite documentos (gastos).
    """
    id_proveedor = models.AutoField(primary_key=True)

    class TipoProveedor(models.TextChoices):
        PERSONA = 'persona', 'Persona'
        EMPRESA = 'empresa', 'Empresa'

    tipo = models.CharField(
        max_length=10,
        choices=TipoProveedor.choices,
        default=TipoProveedor.EMPRESA
    )
    rut_base = models.IntegerField()
    rut_dv = models.CharField(max_length=1)
    nombre = models.CharField(max_length=140)
    giro = models.CharField(max_length=140, null=True, blank=True)
    email = models.EmailField(max_length=120, null=True, blank=True)
    telefono = models.CharField(max_length=40, null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.rut_base}-{self.rut_dv})"

    class Meta:
        db_table = 'proveedor'
        # Restricción del SQL
        unique_together = ('rut_base', 'rut_dv')
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

# --- FIN: Modelos de Negocio (Gastos y Pagos) ---


# --- INICIO: Modelos de Suscripción (SaaS) ---

class CatPlan(models.Model):
    """
    [NUEVA TABLA - SaaS]
    Catálogo de los planes de suscripción pre-definidos.
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
    max_grupos = models.PositiveSmallIntegerField(
        default=3,
        help_text="Número máximo de grupos (torres, etapas) permitidos"
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
    max_grupos = models.PositiveSmallIntegerField(
        default=3,
        help_text="Límite real de grupos (torres, etapas) para ESTA suscripción"
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


# --- INICIO: Modelos de Gastos (Sprint 2) ---

class GastoCategoria(models.Model):
    """
    [MAPEO: Tabla 'gasto_categoria']
    Categorías para agrupar gastos (ej: 'Reparaciones', 'Sueldos', 'Jardinería').
    """
    id_gasto_categ = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60, unique=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'gasto_categoria'
        verbose_name = 'Categoría de Gasto'
        verbose_name_plural = 'Categorías de Gastos'

class Gasto(models.Model):
    """
    [MAPEO: Tabla 'gasto']
    Registro de un egreso de dinero del condominio.
    """
    id_gasto = models.AutoField(primary_key=True)
    id_condominio = models.ForeignKey(
        Condominio,
        on_delete=models.RESTRICT, # No borrar el condominio si tiene gastos registrados
        db_column='id_condominio'
    )
    periodo = models.CharField(
        max_length=6,
        help_text="Periodo contable formato YYYYMM (ej: 202511)"
    )
    id_gasto_categ = models.ForeignKey(
        GastoCategoria,
        on_delete=models.RESTRICT, # No borrar la categoría si se usa en gastos
        db_column='id_gasto_categ',
        verbose_name='Categoría'
    )
    id_proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_proveedor',
        verbose_name='Proveedor'
    )
    id_doc_tipo = models.ForeignKey(
        CatDocTipo,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column='id_doc_tipo',
        verbose_name='Tipo Documento'
    )
    documento_folio = models.CharField(max_length=40, null=True, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)
    fecha_venc = models.DateField(null=True, blank=True, verbose_name="Fecha Vencimiento")
    
    neto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # 'total' es una columna generada en SQL. En Django la calculamos antes de guardar.
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    descripcion = models.CharField(max_length=300, null=True, blank=True)
    evidencia_url = models.URLField(max_length=500, null=True, blank=True)

    def save(self, *args, **kwargs):
        # Lógica de Negocio: El total siempre es la suma de neto + iva
        self.total = self.neto + self.iva
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Gasto #{self.id_gasto} - {self.descripcion[:20]}..."

    class Meta:
        db_table = 'gasto'
        verbose_name = 'Gasto'
        verbose_name_plural = 'Gastos'
        indexes = [
            # Índice para búsquedas rápidas por condominio y periodo (Dashboards)
            models.Index(fields=['id_condominio', 'periodo'], name='ix_gasto_periodo'),
        ]

# --- FIN: Modelos de Gastos ---