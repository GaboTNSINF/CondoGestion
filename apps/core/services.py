from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from .models import (
    Unidad, ProrrateoRegla, ProrrateoFactorUnidad, CatConceptoCargo,
    Gasto, Cobro, CobroDetalle, CargoUnidad, CatCobroEstado, Pago, PagoAplicacion, CatEstadoTx,
    CatMetodoPago
)

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

@transaction.atomic
def generar_cierre_mensual(condominio, periodo):
    """
    Genera los cobros mensuales (Gastos Comunes) para un periodo dado.
    1. Suma todos los gastos del periodo.
    2. Obtiene la regla de prorrateo (Gasto Común) vigente.
    3. Distribuye el total de gastos entre las unidades.
    4. Crea los registros de Cobro y CobroDetalle.
    """

    # 1. Sumar gastos del periodo
    # TODO: Filtrar solo gastos no anulados si existiera estado
    total_gastos = Gasto.objects.filter(
        id_condominio=condominio,
        periodo=periodo
    ).aggregate(Sum('total'))['total__sum'] or Decimal(0)

    if total_gastos <= 0:
        # Podríamos permitir cierre en 0, pero por ahora asumimos que debe haber gastos
        # O simplemente generamos cobros en 0.
        pass

    # 2. Obtener regla de prorrateo vigente
    # Asumimos una única regla ordinaria por defecto por ahora
    # En un sistema real, buscaríamos la regla activa para la fecha del periodo
    regla_prorrateo = ProrrateoRegla.objects.filter(
        id_condominio=condominio,
        tipo=ProrrateoRegla.TipoProrrateo.ORDINARIO
    ).first()

    if not regla_prorrateo:
        # Si no existe, intentamos crear la default
        regla_prorrateo = crear_regla_gasto_comun_default(condominio)

    # Aseguramos que existan factores
    if not ProrrateoFactorUnidad.objects.filter(id_prorrateo=regla_prorrateo).exists():
        calcular_factores_prorrateo(regla_prorrateo)

    factores = ProrrateoFactorUnidad.objects.filter(id_prorrateo=regla_prorrateo)

    # Estado inicial del cobro (ej: 'EMITIDO' o 'BORRADOR')
    # Vamos a asumir 'BORRADOR' o 'POR_PAGAR'.
    # Creemos el estado si no existe
    estado_pendiente, _ = CatCobroEstado.objects.get_or_create(codigo='PENDIENTE')

    cobros_generados = []

    # 3. Iterar por cada unidad y generar su cobro
    for factor_obj in factores:
        unidad = factor_obj.id_unidad
        factor = factor_obj.factor

        # Monto a cobrar a esta unidad
        monto_prorrateado = total_gastos * factor
        # Redondear (en Chile se usa peso entero, en otros lados 2 decimales)
        # Usaremos 0 decimales para pesos (CLP) o 2 para USD según configuración,
        # por defecto del modelo es 2 decimales.
        monto_prorrateado = round(monto_prorrateado, 0)

        # Crear el Cobro (Cabecera)
        # Usamos update_or_create para permitir re-generar el cierre (idempotencia básica)
        cobro, created = Cobro.objects.update_or_create(
            id_unidad=unidad,
            periodo=periodo,
            tipo=Cobro.TipoCobro.MENSUAL,
            defaults={
                'id_cobro_estado': estado_pendiente,
                'id_prorrateo': regla_prorrateo,
                'total_cargos': monto_prorrateado, # Por ahora solo este cargo
                'saldo': monto_prorrateado,        # Asumiendo 0 pagos previos
                'observacion': f"Cierre Mensual {periodo}"
            }
        )

        # Crear el Detalle (Cargo por Gasto Común)
        # Primero creamos el CargoUnidad (Registro histórico del cargo)
        cargo_uni, _ = CargoUnidad.objects.update_or_create(
            id_unidad=unidad,
            periodo=periodo,
            id_concepto_cargo=regla_prorrateo.id_concepto_cargo,
            defaults={
                'monto': monto_prorrateado,
                'detalle': f"Gasto Común Prorrateado (Factor: {factor:.6f})"
            }
        )

        # Luego el detalle en el cobro
        CobroDetalle.objects.update_or_create(
            id_cobro=cobro,
            tipo=CobroDetalle.TipoDetalle.CARGO_COMUN,
            id_cargo_uni=cargo_uni,
            defaults={
                'monto': monto_prorrateado,
                'glosa': "Gasto Común del Periodo"
            }
        )

        cobros_generados.append(cobro)

    return cobros_generados

@transaction.atomic
def registrar_pago(unidad, monto, metodo_pago, fecha_pago, observacion=None):
    """
    Registra un pago y lo aplica a la deuda más antigua (FIFO).
    """
    # 1. Crear el registro de Pago
    pago = Pago.objects.create(
        id_unidad=unidad,
        monto=monto,
        id_metodo_pago=metodo_pago,
        fecha_pago=fecha_pago,
        observacion=observacion,
        tipo=Pago.TipoPago.NORMAL
    )

    monto_disponible = monto

    # 2. Buscar cobros con saldo > 0, ordenados por fecha de emisión (los más antiguos primero)
    # Asumimos que 'id_cobro' autoincremental refleja el orden cronológico de creación también,
    # o usamos 'emitido_at'.
    cobros_pendientes = Cobro.objects.filter(
        id_unidad=unidad,
        saldo__gt=0
    ).order_by('emitido_at', 'id_cobro')

    estado_pagado, _ = CatCobroEstado.objects.get_or_create(codigo='PAGADO')

    # 3. Aplicar pago a las deudas
    for cobro in cobros_pendientes:
        if monto_disponible <= 0:
            break

        saldo_cobro = cobro.saldo

        if monto_disponible >= saldo_cobro:
            # Pagamos el cobro completo
            monto_a_aplicar = saldo_cobro
            monto_disponible -= saldo_cobro

            cobro.saldo = 0
            cobro.total_pagado += monto_a_aplicar
            cobro.id_cobro_estado = estado_pagado
            cobro.save()
        else:
            # Pago parcial del cobro
            monto_a_aplicar = monto_disponible
            monto_disponible = 0

            cobro.saldo -= monto_a_aplicar
            cobro.total_pagado += monto_a_aplicar
            # Estado sigue siendo pendiente/parcial, no cambiamos a PAGADO
            cobro.save()

        # Crear registro de aplicación
        PagoAplicacion.objects.create(
            id_pago=pago,
            id_cobro=cobro,
            monto_aplicado=monto_a_aplicar
        )

    # Si queda saldo a favor (monto_disponible > 0), queda como abono en el pago (no aplicado).
    # En un sistema real, se generaría un 'Saldo a Favor' para futuros cobros.
    # Aquí simplemente queda registrado el pago con monto mayor a lo aplicado.

    return pago
