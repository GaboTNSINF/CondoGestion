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
    
    # --- PRECIOS Y LÍMITES BASE DEL PLAN ---
    # Este es el precio que cobramos por este paquete CERRADO
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

    # Banderas de funcionalidad (ej: {'has_concierge': true, 'allow_voting': false})
    features_json = models.JSONField(
        default=dict,
        help_text="Banderas JSON que definen qué módulos incluye este plan"
    )
    
    # Es la bandera para identificar el "Planificador"
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
    Aquí se guardan los límites y el precio final que el cliente paga.
    """
    id_suscripcion = models.AutoField(primary_key=True)

    # Conectamos la suscripción con el Usuario (admin) que paga
    id_usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, # Referencia al modelo 'Usuario'
        on_delete=models.PROTECT, # No borrar un usuario si tiene una suscripción
        db_column='id_usuario',
        help_text="El usuario (administrador) dueño de esta suscripción"
    )
    
    # Conectamos al plan "plantilla" que eligió (ej: "Pro" o "Planificador")
    id_plan = models.ForeignKey(
        CatPlan,
        on_delete=models.PROTECT, # No borrar planes si están en uso
        db_column='id_plan',
        help_text="El plan base o plantilla seleccionado"
    )
    
    # --- ESTADO Y FECHAS ---
    class EstadoSuscripcion(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        PRUEBA = 'prueba', 'En Prueba'
        CANCELADA = 'cancelada', 'Cancelada' # Cliente se dio de baja
        VENCIDA = 'vencida', 'Vencida' # Dejó de pagar

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

    # --- LÍMITES Y PRECIO FINAL (¡LA CLAVE!) ---
    # Estos campos son los que realmente mandan.
    # Se copian del CatPlan o se definen "a mano" con el Planificador.
    
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

    # Las features finales de ESTA suscripción
    features_json = models.JSONField(
        default=dict,
        help_text="Banderas JSON que definen los módulos de ESTA suscripción"
    )
    
    creado_at = models.DateTimeField(auto_now_add=True)
    actualizado_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # --- ¡MEJORA APLICADA! ---
        # Usamos un 'try/except' para evitar que el admin se rompa
        # si una suscripción se queda sin usuario por error.
        try:
            return f"Suscripción de {self.id_usuario.email} ({self.estado})"
        except Exception:
            return f"Suscripción ID: {self.id_suscripcion} ({self.estado})"

    class Meta:
        db_table = 'suscripcion'
        verbose_name = 'Suscripción de Usuario'
        verbose_name_plural = 'Suscripciones de Usuario'

# --- FIN: Modelos de Suscripción (SaaS) ---