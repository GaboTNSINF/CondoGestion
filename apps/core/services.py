from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from .models import (
    Unidad, ProrrateoRegla, ProrrateoFactorUnidad, CatConceptoCargo,
    Gasto, Cobro, CobroDetalle, CargoUnidad, CatCobroEstado, Pago, PagoAplicacion, CatEstadoTx,
    CatMetodoPago, InteresRegla, ParamReglamento, FondoReservaMov
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

def calcular_intereses_mora(cobro_actual: Cobro, periodo_actual: str):
    """
    Calcula el interés por mora basado en deudas anteriores pendientes
    y agrega el detalle al cobro actual.
    """
    unidad = cobro_actual.id_unidad
    condominio = unidad.id_grupo.id_condominio

    # 1. Buscar si hay deuda vencida (cobros anteriores con saldo > 0)
    deuda_vencida_qs = Cobro.objects.filter(
        id_unidad=unidad,
        saldo__gt=0,
        periodo__lt=periodo_actual # Solo periodos anteriores
    )

    if not deuda_vencida_qs.exists():
        return Decimal(0)

    total_deuda_vencida = deuda_vencida_qs.aggregate(Sum('saldo'))['saldo__sum'] or Decimal(0)

    if total_deuda_vencida <= 0:
        return Decimal(0)

    # 2. Buscar regla de interés vigente para el segmento de la unidad
    # Asumimos fecha actual o primer día del periodo para vigencia
    # TODO: Parsear periodo YYYYMM a date real
    hoy = timezone.now().date()

    regla_interes = InteresRegla.objects.filter(
        id_condominio=condominio,
        id_segmento=unidad.id_segmento,
        vigente_desde__lte=hoy
    ).filter(
        Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)
    ).first()

    if not regla_interes:
        # No hay regla de interés, no se cobra
        return Decimal(0)

    # 3. Calcular Interés
    # Interés Simple Mensual = Deuda * (TasaAnual / 12) / 100
    tasa_anual = regla_interes.tasa_anual_pct
    interes_mensual_pct = tasa_anual / Decimal(12)

    monto_interes = total_deuda_vencida * (interes_mensual_pct / Decimal(100))

    # Redondeo (peso entero)
    monto_interes = round(monto_interes, 0)

    if monto_interes <= 0:
        return Decimal(0)

    # 4. Agregar detalle al cobro actual
    CobroDetalle.objects.update_or_create(
        id_cobro=cobro_actual,
        tipo=CobroDetalle.TipoDetalle.INTERES_MORA,
        defaults={
            'monto': monto_interes,
            'glosa': f"Interés por mora {tasa_anual}% anual sobre deuda vencida de ${total_deuda_vencida:,.0f}",
            # 'id_interes_regla': regla_interes # Si agregáramos el campo al modelo
        }
    )

    # Actualizar total de intereses en la cabecera
    cobro_actual.total_interes = monto_interes

    return monto_interes

def aplicar_fondo_reserva(condominio, total_gastos, periodo):
    """
    Calcula el recargo por fondo de reserva y registra el movimiento.
    Retorna el monto del recargo.
    """
    # 1. Obtener porcentaje del Reglamento
    # Si no existe param, usamos 5% por defecto
    try:
        param = ParamReglamento.objects.get(id_condominio=condominio)
        porcentaje = param.recargo_fondo_reserva_pct
    except ParamReglamento.DoesNotExist:
        # Crear con default 5%
        param = ParamReglamento.objects.create(id_condominio=condominio)
        porcentaje = param.recargo_fondo_reserva_pct

    if porcentaje <= 0:
        return Decimal(0)

    # 2. Calcular Monto
    monto_fondo = total_gastos * (porcentaje / Decimal(100))
    monto_fondo = round(monto_fondo, 0) # Redondeo a entero

    if monto_fondo <= 0:
        return Decimal(0)

    # 3. Registrar Movimiento de Abono al Fondo (Provisionado)
    # Usamos 'ABONO' porque es dinero que ENTRA al fondo (aunque sale del bolsillo del copropietario)
    # Revisar si ya existe para el periodo para evitar duplicados
    FondoReservaMov.objects.update_or_create(
        id_condominio=condominio,
        periodo=periodo,
        tipo='ABONO',
        defaults={
            'fecha': timezone.now(),
            'monto': monto_fondo,
            'glosa': f"Recargo {porcentaje}% Fondo Reserva sobre gastos de {periodo}"
        }
    )

    return monto_fondo

@transaction.atomic
def generar_cierre_mensual(condominio, periodo):
    """
    Genera los cobros mensuales (Gastos Comunes) para un periodo dado.
    1. Suma todos los gastos del periodo.
    2. Calcula Fondo de Reserva y lo suma al total a prorratear.
    3. Distribuye el total (Gastos + FR) entre las unidades.
    4. Crea los registros de Cobro y CobroDetalle.
    5. Calcula intereses por mora sobre deudas anteriores.
    """

    # 1. Sumar gastos del periodo
    total_gastos_operacionales = Gasto.objects.filter(
        id_condominio=condominio,
        periodo=periodo
    ).aggregate(Sum('total'))['total__sum'] or Decimal(0)

    # 2. Calcular Fondo de Reserva
    monto_fondo_reserva = aplicar_fondo_reserva(condominio, total_gastos_operacionales, periodo)

    # TOTAL A PRORRATEAR = Gastos + Fondo Reserva
    total_a_prorratear = total_gastos_operacionales + monto_fondo_reserva

    # 3. Obtener regla de prorrateo vigente
    regla_prorrateo = ProrrateoRegla.objects.filter(
        id_condominio=condominio,
        tipo=ProrrateoRegla.TipoProrrateo.ORDINARIO
    ).first()

    if not regla_prorrateo:
        regla_prorrateo = crear_regla_gasto_comun_default(condominio)

    if not ProrrateoFactorUnidad.objects.filter(id_prorrateo=regla_prorrateo).exists():
        calcular_factores_prorrateo(regla_prorrateo)

    factores = ProrrateoFactorUnidad.objects.filter(id_prorrateo=regla_prorrateo)

    estado_pendiente, _ = CatCobroEstado.objects.get_or_create(codigo='PENDIENTE')

    cobros_generados = []

    # 4. Iterar por cada unidad y generar su cobro base
    for factor_obj in factores:
        unidad = factor_obj.id_unidad
        factor = factor_obj.factor

        monto_prorrateado = round(total_a_prorratear * factor, 0)

        # Crear/Actualizar Cabecera
        cobro, created = Cobro.objects.update_or_create(
            id_unidad=unidad,
            periodo=periodo,
            tipo=Cobro.TipoCobro.MENSUAL,
            defaults={
                'id_cobro_estado': estado_pendiente,
                'id_prorrateo': regla_prorrateo,
                'total_cargos': monto_prorrateado,
                'saldo': 0,
                'observacion': f"Cierre Mensual {periodo}"
            }
        )

        # Detalle Gasto Común (Incluye FR implícito en el prorrateo general)
        # Nota: Idealmente desglosaríamos en el detalle "Gasto Op" y "Fondo Reserva",
        # pero para simplificar el MVP, prorrateamos el total.
        # Si se requiere desglose, habría que crear dos CargoUnidad por persona.
        # Vamos a dejarlo como un solo cargo "Gasto Común" que incluye todo.

        cargo_uni, _ = CargoUnidad.objects.update_or_create(
            id_unidad=unidad,
            periodo=periodo,
            id_concepto_cargo=regla_prorrateo.id_concepto_cargo,
            defaults={
                'monto': monto_prorrateado,
                'detalle': f"Gasto Común (Inc. Fondo Reserva) - Factor: {factor:.6f}"
            }
        )

        CobroDetalle.objects.update_or_create(
            id_cobro=cobro,
            tipo=CobroDetalle.TipoDetalle.CARGO_COMUN,
            id_cargo_uni=cargo_uni,
            defaults={
                'monto': monto_prorrateado,
                'glosa': "Gasto Común del Periodo"
            }
        )

        # 5. Calcular Intereses por Mora
        interes = calcular_intereses_mora(cobro, periodo)

        # Recalcular Totales Finales del Cobro
        cobro.total_cargos = monto_prorrateado
        cobro.total_interes = interes

        total_a_pagar = cobro.total_cargos + cobro.total_interes - cobro.total_descuentos

        cobro.saldo = total_a_pagar - cobro.total_pagado

        cobro.save()
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
