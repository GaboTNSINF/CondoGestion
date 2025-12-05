# apps/core/scripts/setup_dev_data.py
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.core.models import Condominio, Grupo, Unidad, ProrrateoRegla, CatConceptoCargo, CatCobroEstado
from apps.core.services import generar_cierre_mensual

def run(*args, **kwargs):
    """
    Crea un superusuario y datos de prueba para el entorno de desarrollo.
    """
    User = get_user_model()
    email = "admin@test.com"
    password = "password"

    if not User.objects.filter(email=email).exists():
        print(f"Creando superusuario de desarrollo: {email}")
        User.objects.create_superuser(
            email=email,
            password=password,
            rut_base=1,
            rut_dv='9',
            nombres='Admin',
            apellidos='Test'
        )
    else:
        print(f"Superusuario '{email}' ya existe.")

    # Crear datos de prueba para el condominio
    condominio_nombre = "Condominio de Desarrollo"
    condominio, created = Condominio.objects.get_or_create(nombre=condominio_nombre)

    if created:
        print(f"Condominio '{condominio_nombre}' creado.")
        grupo = Grupo.objects.create(id_condominio=condominio, nombre="Torre Dev", tipo="Torre")
        Unidad.objects.create(
            id_grupo=grupo,
            codigo="101-DEV",
            coef_prop=Decimal("0.1")
        )

        # Crear los objetos necesarios para generar el cierre
        concepto_gc, _ = CatConceptoCargo.objects.get_or_create(codigo='GASTO_COMUN', nombre='Gasto Común')
        ProrrateoRegla.objects.create(
            id_condominio=condominio,
            id_concepto_cargo=concepto_gc,
            criterio=ProrrateoRegla.CriterioProrrateo.COEF_PROP,
            vigente_desde="2023-01-01"
        )
        CatCobroEstado.objects.get_or_create(codigo='PENDIENTE')

        # Generar un cierre para que el botón de PDF sea visible
        try:
            print("Generando cierre mensual de prueba...")
            generar_cierre_mensual(condominio, "202512")
            print("Cierre de prueba generado exitosamente.")
        except Exception as e:
            print(f"Error generando cierre de prueba: {e}")
    else:
        print(f"Condominio '{condominio_nombre}' ya existe.")
