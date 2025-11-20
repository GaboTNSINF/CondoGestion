from decimal import Decimal
from django.db import transaction
from .models import Unidad, ProrrateoRegla, ProrrateoFactorUnidad, CatConceptoCargo

def calcular_factores_prorrateo(prorrateo_regla: ProrrateoRegla):
    """
    Calcula y guarda los factores de prorrateo para cada unidad
    según el criterio definido en la regla.
    """

    condominio = prorrateo_regla.id_condominio
    criterio = prorrateo_regla.criterio

    # Obtenemos todas las unidades del condominio
    unidades = Unidad.objects.filter(id_grupo__id_condominio=condominio)

    if not unidades.exists():
        return 0

    factores = []

    # Limpiamos factores anteriores si existen (para evitar duplicados o inconsistencias al recalcular)
    ProrrateoFactorUnidad.objects.filter(id_prorrateo=prorrateo_regla).delete()

    if criterio == ProrrateoRegla.CriterioProrrateo.COEF_PROP:
        # Distribución según Coeficiente de Propiedad (Alícuota)
        # Simplemente copiamos el coef_prop de la unidad al factor
        for unidad in unidades:
            factores.append(ProrrateoFactorUnidad(
                id_prorrateo=prorrateo_regla,
                id_unidad=unidad,
                factor=unidad.coef_prop
            ))

    elif criterio == ProrrateoRegla.CriterioProrrateo.IGUALITARIO:
        # Distribución Igualitaria (1 / N)
        cantidad_unidades = unidades.count()
        if cantidad_unidades > 0:
            factor_igual = Decimal(1) / Decimal(cantidad_unidades)
            # Redondeamos a 6 decimales para guardar
            factor_igual = round(factor_igual, 6)

            for unidad in unidades:
                factores.append(ProrrateoFactorUnidad(
                    id_prorrateo=prorrateo_regla,
                    id_unidad=unidad,
                    factor=factor_igual
                ))

    # TODO: Implementar otros criterios (POR_M2, POR_TIPO, MONTO_FIJO) si es necesario
    # Por ahora el MVP probablemente usa COEF_PROP que es lo legal estándar

    # Guardamos masivamente
    ProrrateoFactorUnidad.objects.bulk_create(factores)

    return len(factores)

def crear_regla_gasto_comun_default(condominio):
    """
    Crea una regla de prorrateo por defecto para 'Gasto Común' usando 'Coeficiente de Propiedad'
    si no existe.
    """
    concepto_gc, _ = CatConceptoCargo.objects.get_or_create(
        codigo='GASTO_COMUN',
        defaults={'nombre': 'Gasto Común'}
    )

    regla, created = ProrrateoRegla.objects.get_or_create(
        id_condominio=condominio,
        id_concepto_cargo=concepto_gc,
        tipo=ProrrateoRegla.TipoProrrateo.ORDINARIO,
        defaults={
            'criterio': ProrrateoRegla.CriterioProrrateo.COEF_PROP,
            'vigente_desde': '2023-01-01', # Fecha arbitraria inicial
            'descripcion': 'Regla base de Gasto Común por Coeficiente de Propiedad'
        }
    )

    if created:
        calcular_factores_prorrateo(regla)

    return regla
