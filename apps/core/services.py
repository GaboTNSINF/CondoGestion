from decimal import Decimal
from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone
from .models import (
    Unidad, ProrrateoRegla, ProrrateoFactorUnidad, CatConceptoCargo,
    Gasto, Cobro, CobroDetalle, CargoUnidad, CatCobroEstado, Pago, PagoAplicacion, CatEstadoTx,
    CatMetodoPago, InteresRegla, ParamReglamento, FondoReservaMov, Auditoria, CondominioAnexoRegla,
    Notificacion, ResumenMensual
)

def get_proximo_periodo(condominio):
    """
    Determina el próximo periodo a cerrar (YYYYMM).
    Busca el último Cobro o ResumenMensual.
    Si existe: ultimo + 1 mes.
    Si no: Mes actual.
    """
    # Check last ResumenMensual (Closed month)
    last_resumen = ResumenMensual.objects.filter(id_condominio=condominio).order_by('-periodo').first()
    last_cobro = Cobro.objects.filter(id_unidad__id_grupo__id_condominio=condominio).order_by('-periodo').first()

    last_period = None
    if last_resumen:
        last_period = last_resumen.periodo

    if last_cobro:
        if not last_period or last_cobro.periodo > last_period:
            last_period = last_cobro.periodo

    if not last_period:
        # No history, use current month
        return timezone.now().strftime("%Y%m")

    # Calculate next month
    # Format YYYYMM
    try:
        year = int(last_period[:4])
        month = int(last_period[4:])

        month += 1
        if month > 12:
            month = 1
            year += 1

        return f"{year}{month:02d}"
    except (ValueError, IndexError):
        # Fallback
        return timezone.now().strftime("%Y%m")

def registrar_auditoria(entidad, entidad_id, accion, usuario, detalle=None):
    """
    Registra una acción en la tabla de auditoría.
    """
    try:
        Auditoria.objects.create(
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            id_usuario=usuario if usuario and usuario.is_authenticated else None,
            usuario_email=usuario.email if usuario and usuario.is_authenticated else 'sistema',
            detalle=detalle
        )
    except Exception as e:
        # En producción, usar logging.error. No queremos romper la transacción principal si falla la auditoría
        # pero en "Security Zero Trust" quizás sí. Para este MVP, lo dejamos silencioso o print.
        print(f"Error auditando: {e}")

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
    monto_fondo = total_gastos * (Decimal(porcentaje) / Decimal(100))
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

    # TODO: Recuperar usuario actual del request si fuera posible, pero en services es difícil sin pasar contexto.
    # Asumiremos 'None' (Sistema) o pasaremos el usuario como argumento en refactor futuro.

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

    # Calcular Cobros por Anexos Extra (Bodegas/Estacionamientos)
    calcular_cobro_anexos(condominio, periodo)

    # --- VALIDACIÓN CRÍTICA ---
    # Si después de todo el proceso no se generó ningún cobro, es un error.
    # La causa más común es que no hay Unidades registradas en el Condominio.
    if not cobros_generados:
        raise ValueError(
            "No se generó ningún cobro. "
            "Verifique que existan Unidades (departamentos) registradas en este condominio "
            "antes de generar un cierre."
        )

    # Auditoría masiva (simplificada)
    registrar_auditoria(
        entidad='Cobro',
        entidad_id=0, # 0 indicando masivo
        accion='CREATE',
        usuario=None,
        detalle={'periodo': periodo, 'cantidad_generada': len(cobros_generados)}
    )

    # --- NOTIFICACIONES ---
    # 1. Notificar Administradores
    # Buscar usuarios admin de este condominio (Modelo UsuarioAdminCondo no importado, pero podemos navegar)
    # Ojo: UsuarioAdminCondo esta en usuarios.models y no podemos importarlo circularmente facil.
    # Usaremos un filtro genérico si es posible o importamos dentro de la función.
    from apps.usuarios.models import UsuarioAdminCondo, Copropietario, Residencia

    admins = UsuarioAdminCondo.objects.filter(id_condominio=condominio).select_related('id_usuario')
    for admin_rel in admins:
        Notificacion.objects.create(
            usuario=admin_rel.id_usuario,
            titulo="Cierre Mensual Generado",
            mensaje=f"Se ha generado el cierre mensual del periodo {periodo} para {condominio.nombre}. Total cobrado: {len(cobros_generados)} unidades."
        )

    # 2. Notificar Residentes (Copropietarios y Arrendatarios)
    # Iteramos sobre los cobros generados para saber a quién notificar
    for cobro in cobros_generados:
        unidad = cobro.id_unidad
        # Buscar residentes activos
        # Prioridad: Residentes (viven ahi) > Copropietarios (dueños)
        # La lógica pedida: "Recibe aviso de 'Cobro Generado' (con el monto) al cerrar el mes."

        destinatarios = set()

        # Buscar residentes
        residentes = Residencia.objects.filter(id_unidad=unidad, hasta__isnull=True)
        for res in residentes:
            destinatarios.add(res.id_usuario)

        # Si no hay residente, notificar copropietario
        if not residentes.exists():
            coprops = Copropietario.objects.filter(id_unidad=unidad, hasta__isnull=True)
            for cop in coprops:
                destinatarios.add(cop.id_usuario)

        for usuario_dest in destinatarios:
            Notificacion.objects.create(
                usuario=usuario_dest,
                titulo="Gastos Comunes Disponibles",
                mensaje=f"Se ha generado el cobro de Gastos Comunes para su unidad {unidad.codigo}. Periodo: {periodo}. Total a pagar: ${cobro.saldo:,.0f}"
            )

    return cobros_generados

def calcular_cobro_anexos(condominio, periodo):
    """
    Genera cargos adicionales por anexos (estacionamientos/bodegas)
    según las reglas definidas en CondominioAnexoRegla.
    """
    # 1. Buscar reglas vigentes
    # Simplificación: Solo reglas activas "hoy", idealmente check vs periodo
    hoy = timezone.now().date()

    reglas = CondominioAnexoRegla.objects.filter(
        id_condominio=condominio,
        vigente_desde__lte=hoy
    ).filter(
        Q(vigente_hasta__isnull=True) | Q(vigente_hasta__gte=hoy)
    )

    if not reglas.exists():
        return 0

    cargo_generados = 0

    # Buscamos un concepto de cargo para 'Uso Espacios Comunes' o similar, o creamos uno genérico
    concepto_anexo, _ = CatConceptoCargo.objects.get_or_create(
        codigo='ANEXO_EXTRA',
        defaults={'nombre': 'Cobro Anexo Extra'}
    )

    # --- CORRECCIÓN IDEMPOTENCIA ---
    # Antes de generar nuevos cargos por anexos para este periodo, eliminamos los generados automáticamente
    # en corridas previas. Buscamos por condominio, periodo, concepto y tipo EXTRA.
    # Nota: Esto asume que "ANEXO_EXTRA" solo se usa aquí.
    cargos_previos = CargoUnidad.objects.filter(
        id_unidad__id_grupo__id_condominio=condominio,
        periodo=periodo,
        id_concepto_cargo=concepto_anexo,
        tipo=CargoUnidad.TipoCargo.EXTRA
    )

    # Primero borramos los CobroDetalle asociados para evitar huérfanos (aunque SET_NULL está activado,
    # queremos borrar la línea del detalle también).
    CobroDetalle.objects.filter(id_cargo_uni__in=cargos_previos).delete()

    # Luego borramos los CargoUnidad
    cargos_previos.delete()
    # --- FIN CORRECCIÓN ---

    for regla in reglas:
        # Buscar unidades que coincidan con el subtipo de la regla
        unidades_target = Unidad.objects.filter(
            id_grupo__id_condominio=condominio
        )

        if regla.id_viv_subtipo:
            unidades_target = unidades_target.filter(id_viv_subtipo=regla.id_viv_subtipo)

        # Filtramos las que tienen flag de cobrable (Asumiendo que este flag activa la regla)
        unidades_cobrables = unidades_target.filter(anexo_cobrable=True)

        for unidad in unidades_cobrables:
            # Recuperar el cobro mensual de esta unidad para este periodo
            # Debe existir porque acabamos de correr generar_cierre_mensual antes
            cobro = Cobro.objects.filter(
                id_unidad=unidad,
                periodo=periodo
            ).first()

            if not cobro:
                continue

            # Determinar monto.
            # Como el modelo NO tiene campo de monto explícito, asumiremos un valor fijo
            # o "Placeholder" para cumplir la lógica de negocio solicitada.
            # En un caso real, el monto vendría de la Regla o de un parámetro global.
            # Usaremos 10.000 como valor por defecto de "Multa/Cobro" por anexo extra.
            monto_cargo = Decimal(10000)

            # Crear Cargo Unidad
            cargo_uni = CargoUnidad.objects.create(
                id_unidad=unidad,
                periodo=periodo,
                id_concepto_cargo=concepto_anexo,
                tipo=CargoUnidad.TipoCargo.EXTRA,
                monto=monto_cargo,
                detalle=f"Cargo por {regla.get_anexo_tipo_display()} adicional ({regla.comentario or 'S/C'})"
            )

            # Agregar al detalle del Cobro
            CobroDetalle.objects.create(
                id_cobro=cobro,
                tipo=CobroDetalle.TipoDetalle.CARGO_INDIVIDUAL, # O Ajuste
                id_cargo_uni=cargo_uni,
                monto=monto_cargo,
                glosa=f"Cobro adicional {regla.get_anexo_tipo_display()}"
            )

            # Actualizar totales del Cobro
            cobro.total_cargos += monto_cargo
            cobro.saldo += monto_cargo
            cobro.save()

            cargo_generados += 1

    return cargo_generados

@transaction.atomic
def crear_gasto(condominio, form, usuario):
    """
    Crea un gasto a partir de un formulario validado y registra la auditoría.
    Auto-calcula el periodo basado en la fecha de emisión si no viene en el form.
    Calcula Neto e IVA desde monto_total.
    """
    gasto = form.save(commit=False)
    gasto.id_condominio = condominio

    # Auto-calculate period if not present or empty
    if not gasto.periodo and gasto.fecha_emision:
        gasto.periodo = gasto.fecha_emision.strftime("%Y%m")

    # Calculate Neto/IVA from monto_total (from Form cleaned_data)
    monto_total = form.cleaned_data.get('monto_total')
    if monto_total:
        # Neto = Total / 1.19
        neto = monto_total / Decimal('1.19')
        iva = monto_total - neto

        # Rounding logic (optional but recommended to match currency)
        # Standard for Chile CLP is usually integer but DB stores decimal.
        # We keep decimal precision.
        gasto.neto = neto
        gasto.iva = iva
        # gasto.total is calculated in save() method of model based on neto+iva

    gasto.save()

    # Auditoría
    registrar_auditoria(
        entidad='Gasto',
        entidad_id=gasto.pk,
        accion='CREATE',
        usuario=usuario,
        detalle={'monto': float(gasto.total), 'proveedor': str(gasto.id_proveedor)}
    )
    return gasto

@transaction.atomic
def registrar_pago(unidad, monto, metodo_pago, fecha_pago, observacion=None, usuario=None):
    """
    Registra un pago y lo aplica a la deuda más antigua (FIFO).
    """
    # Calculate period from fecha_pago
    periodo = None
    if hasattr(fecha_pago, 'strftime'):
        periodo = fecha_pago.strftime("%Y%m")
    elif isinstance(fecha_pago, str):
        # Attempt to parse if string (though view passes date object usually)
        pass

    # 1. Crear el registro de Pago
    pago = Pago.objects.create(
        id_unidad=unidad,
        monto=monto,
        id_metodo_pago=metodo_pago,
        fecha_pago=fecha_pago,
        periodo=periodo,
        observacion=observacion,
        tipo=Pago.TipoPago.NORMAL
    )

    registrar_auditoria(
        entidad='Pago',
        entidad_id=pago.pk,
        accion='CREATE',
        usuario=usuario,
        detalle={'monto': float(monto), 'unidad': unidad.codigo}
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

    # --- NOTIFICACIONES ---
    # Notificar al residente "Pago Recibido"
    from apps.usuarios.models import Residencia, Copropietario
    destinatarios = set()
    residentes = Residencia.objects.filter(id_unidad=unidad, hasta__isnull=True)
    for res in residentes:
        destinatarios.add(res.id_usuario)

    if not destinatarios:
        coprops = Copropietario.objects.filter(id_unidad=unidad, hasta__isnull=True)
        for cop in coprops:
            destinatarios.add(cop.id_usuario)

    for usuario_dest in destinatarios:
        Notificacion.objects.create(
            usuario=usuario_dest,
            titulo="Pago Confirmado",
            mensaje=f"Hemos recibido su pago de ${monto:,.0f} para la unidad {unidad.codigo}. ¡Gracias!"
        )

    return pago

@transaction.atomic
def anular_pago(pago_id, usuario=None):
    """
    Anula un pago existente creando un contra-asiento (Pago tipo AJUSTE negativo).
    No borra físicamente el pago original.
    """
    pago_original = Pago.objects.get(pk=pago_id)

    # Validar si ya está anulado (opcional, pero buena práctica)
    # En este modelo simple, no tenemos estado 'ANULADO', así que permitimos crear el contra-asiento.

    # Crear Contra-Asiento
    contra_pago = Pago.objects.create(
        id_unidad=pago_original.id_unidad,
        monto= -pago_original.monto, # Monto Negativo
        id_metodo_pago=pago_original.id_metodo_pago,
        fecha_pago=timezone.now(),
        periodo=pago_original.periodo,
        tipo=Pago.TipoPago.AJUSTE,
        observacion=f"Anulación/Reversa del Pago #{pago_original.id_pago}",
        ref_externa=f"REV-{pago_original.id_pago}"
    )

    # Revertir aplicaciones (Si el pago original pagó cobros, debemos 'despagarlos' o aumentar su saldo)
    aplicaciones = PagoAplicacion.objects.filter(id_pago=pago_original)

    estado_pendiente, _ = CatCobroEstado.objects.get_or_create(codigo='PENDIENTE')

    for app in aplicaciones:
        cobro = app.id_cobro
        monto_reversado = app.monto_aplicado

        # Devolvemos el saldo al cobro
        cobro.saldo += monto_reversado
        cobro.total_pagado -= monto_reversado

        # Si el saldo vuelve a ser positivo, cambiamos estado a PENDIENTE (o PARCIAL si implementáramos ese estado)
        if cobro.saldo > 0:
             cobro.id_cobro_estado = estado_pendiente

        cobro.save()

        # Registramos la aplicación negativa para trazabilidad
        PagoAplicacion.objects.create(
            id_pago=contra_pago,
            id_cobro=cobro,
            monto_aplicado= -monto_reversado
        )

    registrar_auditoria(
        entidad='Pago',
        entidad_id=pago_original.pk,
        accion='DELETE', # Lógico
        usuario=usuario,
        detalle={'motivo': 'Anulación por usuario', 'contra_pago_id': contra_pago.pk}
    )

    return contra_pago
