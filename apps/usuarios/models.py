# Importamos los módulos base de Django para crear modelos
from django.db import models
# Importamos las clases base para crear un modelo de Usuario personalizado
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# Importamos el settings para poder referirnos al modelo de Usuario
from django.conf import settings

# --- INICIO: Administrador de Usuarios ---

class UsuarioManager(BaseUserManager):
    """
    Este es el "Administrador" de nuestro modelo Usuario.
    Le enseña a Django cómo crear usuarios ("create_user")
    y superusuarios ("create_superuser") usando nuestro modelo personalizado.
    """

    def create_user(self, email, rut_base, rut_dv, nombres, apellidos, password=None, **extra_fields):
        """
        Crea y guarda un Usuario regular con el email, RUT, nombres y password.
        """
        if not email:
            raise ValueError('El campo Email es obligatorio')
        if not rut_base or not rut_dv:
            raise ValueError('El campo RUT es obligatorio')

        email = self.normalize_email(email)
        usuario = self.model(
            email=email,
            rut_base=rut_base,
            rut_dv=rut_dv,
            nombres=nombres,
            apellidos=apellidos,
            **extra_fields
        )
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, rut_base, rut_dv, nombres, apellidos, password, **extra_fields):
        """
        Crea y guarda un Superusuario.
        """
        usuario = self.create_user(
            email=email,
            rut_base=rut_base,
            rut_dv=rut_dv,
            nombres=nombres,
            apellidos=apellidos,
            password=password,
            **extra_fields
        )
        usuario.is_superuser = True
        usuario.is_staff = True 
        usuario.tipo_usuario = 'super_admin'
        usuario.save(using=self._db)
        return usuario

# --- FIN: Administrador de Usuarios ---


# --- INICIO: Modelo de Usuario ---

class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    [MAPEO: Tabla 'usuario']
    Modelo de Usuario personalizado.
    """
    
    # ID: Dejamos que Django maneje el 'id' automáticamente.

    class TipoUsuario(models.TextChoices):
        SUPER_ADMIN = 'super_admin', 'Super Administrador'
        ADMIN = 'admin', 'Administrador'
        USUARIO = 'usuario', 'Usuario' # Residente/Copropietario

    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.USUARIO,
        db_comment="Rol del usuario en el sistema (ej: admin, usuario)"
    )
    rut_base = models.IntegerField(
        db_comment="RUT sin dígito verificador"
    )
    rut_dv = models.CharField(
        max_length=1,
        db_comment="Dígito verificador"
    )
    nombres = models.CharField(max_length=120)
    apellidos = models.CharField(max_length=120)
    email = models.EmailField(
        max_length=120,
        unique=True,
        db_comment="Email de login"
    )
    telefono = models.CharField(max_length=40, blank=True, null=True)
    direccion = models.CharField(max_length=200, blank=True, null=True)

    is_active = models.BooleanField(
        default=True,
        db_comment="Indica si el usuario puede iniciar sesión"
    )
    is_staff = models.BooleanField(
        default=False,
        db_comment="Indica si el usuario puede acceder al panel de admin"
    )
    creado_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="Fecha de creación del registro"
    )
    
    objects = UsuarioManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['rut_base', 'rut_dv', 'nombres', 'apellidos']

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.email})"
    def get_full_name(self):
        return f"{self.nombres} {self.apellidos}"
    def get_short_name(self):
        return self.nombres

    class Meta:
        db_table = 'usuario'
        constraints = [
            models.UniqueConstraint(
                fields=['rut_base', 'rut_dv'], 
                name='uk_usuario_rut'
            )
        ]
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

# --- FIN: Modelo de Usuario ---


# --- INICIO: Modelo UsuarioAdminCondo ---

class UsuarioAdminCondo(models.Model):
    """
    [MAPEO: Tabla 'usuario_admin_condo']
    Tabla pivote que conecta a un Usuario (admin) con los
    Condominios que administra.
    """
    id_usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario'
    )
    id_condominio = models.ForeignKey(
        'core.Condominio', # Referencia en string a 'app.modelo'
        on_delete=models.CASCADE,
        db_column='id_condominio'
    )

    def __str__(self):
        try:
            return f"{self.id_usuario.email} administra {self.id_condominio.nombre}"
        except Exception:
            return f"Relación Admin-Condominio ID: {self.id}"

    class Meta:
        db_table = 'usuario_admin_condo'
        unique_together = ('id_usuario', 'id_condominio')
        verbose_name = 'Admin por Condominio'
        verbose_name_plural = 'Admins por Condominio'

# --- FIN: Modelo UsuarioAdminCondo ---


# --- INICIO: Modelos de Relación Usuario-Unidad --- ¡NUEVOS! ---

class Copropietario(models.Model):
    """
    [MAPEO: Tabla 'copropietario']
    Define la relación de PROPIEDAD de un Usuario
    sobre una Unidad (departamento, bodega, etc.).
    """
    id_coprop = models.AutoField(primary_key=True)
    
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Referencia a 'Usuario'
        on_delete=models.RESTRICT, # Como en el SQL, no borrar usuario si es propietario
        db_column='id_usuario',
        verbose_name='Usuario Propietario'
    )
    
    id_unidad = models.ForeignKey(
        'core.Unidad', # Referencia en string a 'app.modelo'
        on_delete=models.RESTRICT, # No borrar unidad si tiene propietario
        db_column='id_unidad',
        verbose_name='Unidad'
    )
    
    porcentaje = models.DecimalField(
        max_digits=6, 
        decimal_places=3,
        db_comment="Porcentaje de propiedad sobre la unidad (ej: 100.000 o 50.000)"
    )
    
    desde = models.DateField(db_comment="Fecha inicio de propiedad")
    hasta = models.DateField(
        null=True, blank=True, 
        db_comment="Fecha fin de propiedad (si se vendió)"
    )

    def __str__(self):
        try:
            return f"{self.id_usuario.get_full_name()} posee {self.porcentaje}% de U. {self.id_unidad.codigo}"
        except Exception:
            return f"Copropietario ID: {self.id_coprop}"

    class Meta:
        db_table = 'copropietario'
        # Restricción del SQL
        unique_together = ('id_unidad', 'id_usuario', 'desde')
        verbose_name = 'Copropietario'
        verbose_name_plural = 'Copropietarios'

class Residencia(models.Model):
    """
    [MAPEO: Tabla 'residencia']
    Define la relación de RESIDENCIA de un Usuario
    sobre una Unidad (quién vive ahí: el dueño o un arrendatario).
    """
    id_residencia = models.AutoField(primary_key=True)
    
    id_unidad = models.ForeignKey(
        'core.Unidad', # Referencia en string
        on_delete=models.CASCADE, # Como en el SQL, si se borra la unidad, se borra el residente
        db_column='id_unidad',
        verbose_name='Unidad'
    )
    
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Referencia a 'Usuario'
        on_delete=models.CASCADE, # Como en el SQL, si se borra el usuario, se borra el registro de residencia
        db_column='id_usuario',
        verbose_name='Usuario Residente'
    )

    # Definimos el ENUM del SQL
    class OrigenResidencia(models.TextChoices):
        PROPIETARIO = 'propietario', 'Propietario'
        ARRENDATARIO = 'arrendatario', 'Arrendatario'

    origen = models.CharField(
        max_length=20,
        choices=OrigenResidencia.choices,
        db_comment="Indica si el residente es el dueño o un arrendatario"
    )
    
    desde = models.DateField(db_comment="Fecha inicio de residencia")
    hasta = models.DateField(
        null=True, blank=True, 
        db_comment="Fecha fin de residencia"
    )
    
    observacion = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        try:
            return f"{self.id_usuario.get_full_name()} ({self.origen}) vive en U. {self.id_unidad.codigo}"
        except Exception:
            return f"Residencia ID: {self.id_residencia}"

    class Meta:
        db_table = 'residencia'
        # Restricción del SQL
        unique_together = ('id_unidad', 'id_usuario', 'desde')
        verbose_name = 'Residente'
        verbose_name_plural = 'Residentes'

# --- FIN: Modelos de Relación Usuario-Unidad ---

# --- INICIO: Modelo Código de Verificación (2FA) ---

class CodigoVerificacion(models.Model):
    """
    Almacena códigos OTP para validación de acciones críticas (2FA).
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='id_usuario'
    )
    codigo = models.CharField(max_length=6)
    accion = models.CharField(max_length=50) # ej: 'perfil_update'
    creado_at = models.DateTimeField(auto_now_add=True)

    def es_valido(self):
        # Importación tardía para evitar circular imports si los hubiera
        from django.utils import timezone
        import datetime

        # 10 minutos de validez
        expiracion = self.creado_at + datetime.timedelta(minutes=10)
        return timezone.now() <= expiracion

    class Meta:
        db_table = 'codigo_verificacion'
        verbose_name = 'Código de Verificación'
        verbose_name_plural = 'Códigos de Verificación'

# --- FIN: Modelo Código de Verificación (2FA) ---