# apps/core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum

# --- IMPORTANTE: Importamos los modelos para poder buscar datos ---
# Agregamos Auditoria, CondominioAnexoRegla y ParamReglamento como precaución
from .models import (
    Condominio, Gasto, Cobro, Pago, Trabajador, Remuneracion,
    Notificacion, Auditoria, CondominioAnexoRegla, ParamReglamento
)
from .forms import GastoForm, PagoForm, TrabajadorForm, RemuneracionForm
from .services import generar_cierre_mensual, registrar_pago, registrar_auditoria, crear_gasto

# --- INICIO: Vistas del Dashboard ---

@login_required
def index_view(request):
    """
    Vista principal (Dashboard).
    Ahora recupera los condominios de la base de datos.
    """
    
    # 1. Buscamos TODOS los condominios en la base de datos
    lista_condominios = Condominio.objects.all()

    # 2. Preparamos el contexto con el usuario Y la lista
    contexto = {
        'usuario': request.user,
        'mis_condominios': lista_condominios  # <--- Enviamos la lista al HTML
    }
    
    return render(request, 'index.html', contexto)

@login_required
def avisos_list_view(request):
    """
    Muestra las notificaciones del usuario.
    """
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-created_at')

    # Marcar como leídas (opcional, para este MVP simplemente las listamos)
    # notificaciones.update(leido=True)

    return render(request, 'core/avisos_list.html', {'notificaciones': notificaciones})

@login_required
def soporte_view(request):
    """
    Vista estática de soporte.
    """
    return render(request, 'core/soporte.html')

# --- FIN: Vistas del Dashboard ---

# --- INICIO: Vistas de Gastos ---

@login_required
def gastos_list_view(request, condominio_id):
    """
    Vista para listar los gastos de un condominio específico.
    """
    # 1. Obtenemos el condominio o devolvemos 404 si no existe
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    # 2. Obtenemos los gastos asociados a ese condominio
    #    Ordenamos por fecha de emisión descendente (los más recientes primero)
    gastos = Gasto.objects.filter(id_condominio=condominio).order_by('-fecha_emision')

    # 3. Preparamos el contexto
    contexto = {
        'condominio': condominio,
        'gastos': gastos,
        'usuario': request.user
    }

    return render(request, 'core/gastos_list.html', contexto)

@login_required
def gasto_create_view(request, condominio_id):
    """
    Vista para crear un nuevo gasto en un condominio.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    if request.method == 'POST':
        form = GastoForm(request.POST)
        if form.is_valid():
            # Delegamos la creación al servicio para asegurar auditoría
            crear_gasto(condominio, form, request.user)
            return redirect('gastos_list', condominio_id=condominio.id_condominio)
    else:
        form = GastoForm()

    contexto = {
        'form': form,
        'condominio': condominio,
        'usuario': request.user
    }
    return render(request, 'core/gasto_form.html', contexto)

# --- FIN: Vistas de Gastos ---


# --- INICIO: Vistas de Cierre Mensual y Cobros ---

@login_required
def cierre_mensual_view(request, condominio_id):
    """
    Vista para gestionar el cierre mensual.
    Muestra resumen del mes y botón para generar cobros.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    # Periodo por defecto: mes actual o último con movimientos
    # Por simplicidad para el MVP, usaremos un parámetro GET o un hardcode temporal,
    # o idealmente un selector de fechas.
    # Vamos a tomar el parametro 'periodo' del GET, o '202311' como ejemplo.
    periodo = request.GET.get('periodo', '202311') # TODO: Calcular dinámicamente

    # Resumen de gastos
    total_gastos = Gasto.objects.filter(
        id_condominio=condominio,
        periodo=periodo
    ).aggregate(Sum('total'))['total__sum'] or 0

    # Verificar si ya hay cobros generados
    cobros_existentes = Cobro.objects.filter(
        id_unidad__id_grupo__id_condominio=condominio,
        periodo=periodo,
        tipo=Cobro.TipoCobro.MENSUAL
    )
    ya_cerrado = cobros_existentes.exists()
    total_cobrado = cobros_existentes.aggregate(Sum('total_cargos'))['total_cargos__sum'] or 0

    if request.method == 'POST':
        # Generar el cierre
        try:
            generar_cierre_mensual(condominio, periodo)
            messages.success(request, f"Cierre mensual {periodo} generado exitosamente.")
            return redirect('cobros_list', condominio_id=condominio.id_condominio, periodo=periodo)
        except Exception as e:
            messages.error(request, f"Error al generar cierre: {str(e)}")

    contexto = {
        'condominio': condominio,
        'periodo': periodo,
        'total_gastos': total_gastos,
        'ya_cerrado': ya_cerrado,
        'total_cobrado': total_cobrado,
        'cantidad_cobros': cobros_existentes.count()
    }

    return render(request, 'core/cierre_mensual.html', contexto)

@login_required
def cobros_list_view(request, condominio_id, periodo):
    """
    Lista los cobros generados para un condominio y periodo.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    cobros = Cobro.objects.filter(
        id_unidad__id_grupo__id_condominio=condominio,
        periodo=periodo
    ).select_related('id_unidad', 'id_cobro_estado').order_by('id_unidad__codigo')

    contexto = {
        'condominio': condominio,
        'periodo': periodo,
        'cobros': cobros
    }

    return render(request, 'core/cobros_list.html', contexto)

# --- FIN: Vistas de Cierre Mensual y Cobros ---


# --- INICIO: Vistas de Pagos ---

@login_required
def pago_create_view(request, condominio_id):
    """
    Vista para registrar un nuevo pago manualmente.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    if request.method == 'POST':
        form = PagoForm(request.POST, condominio_id=condominio_id)
        if form.is_valid():
            data = form.cleaned_data
            try:
                registrar_pago(
                    unidad=data['id_unidad'],
                    monto=data['monto'],
                    metodo_pago=data['id_metodo_pago'],
                    fecha_pago=data['fecha_pago'],
                    observacion=data['observacion'],
                    usuario=request.user  # Pasamos el usuario para auditoría
                )
                messages.success(request, "Pago registrado exitosamente.")
                return redirect('pagos_list', condominio_id=condominio.id_condominio)
            except Exception as e:
                messages.error(request, f"Error al registrar pago: {str(e)}")
    else:
        form = PagoForm(condominio_id=condominio_id)

    contexto = {
        'form': form,
        'condominio': condominio
    }
    return render(request, 'core/pago_form.html', contexto)

@login_required
def pagos_list_view(request, condominio_id):
    """
    Lista los pagos registrados para un condominio.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    pagos = Pago.objects.filter(
        id_unidad__id_grupo__id_condominio=condominio
    ).select_related('id_unidad', 'id_metodo_pago').order_by('-fecha_pago')

    contexto = {
        'condominio': condominio,
        'pagos': pagos
    }

    return render(request, 'core/pagos_list.html', contexto)

# --- FIN: Vistas de Pagos ---


# --- INICIO: Vistas de RRHH (Trabajadores y Remuneraciones) ---

@login_required
def trabajadores_list_view(request, condominio_id):
    """
    Lista los trabajadores de un condominio.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)
    trabajadores = Trabajador.objects.filter(id_condominio=condominio)

    contexto = {
        'condominio': condominio,
        'trabajadores': trabajadores
    }
    return render(request, 'core/trabajadores_list.html', contexto)

@login_required
def trabajador_create_view(request, condominio_id):
    """
    Vista para registrar un nuevo trabajador.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    if request.method == 'POST':
        form = TrabajadorForm(request.POST)
        if form.is_valid():
            trabajador = form.save(commit=False)
            trabajador.id_condominio = condominio
            trabajador.save()
            messages.success(request, "Trabajador registrado exitosamente.")
            return redirect('trabajadores_list', condominio_id=condominio.id_condominio)
    else:
        form = TrabajadorForm()

    contexto = {
        'condominio': condominio,
        'form': form
    }
    return render(request, 'core/trabajador_form.html', contexto)

@login_required
def remuneraciones_list_view(request, condominio_id):
    """
    Lista las remuneraciones (sueldos) de un condominio.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)
    # Filtramos por trabajadores del condominio
    remuneraciones = Remuneracion.objects.filter(id_trabajador__id_condominio=condominio).order_by('-periodo')

    contexto = {
        'condominio': condominio,
        'remuneraciones': remuneraciones
    }
    return render(request, 'core/remuneraciones_list.html', contexto)

@login_required
def remuneracion_create_view(request, condominio_id):
    """
    Vista para registrar una nueva remuneración.
    """
    condominio = get_object_or_404(Condominio, pk=condominio_id)

    if request.method == 'POST':
        form = RemuneracionForm(request.POST, condominio_id=condominio_id)
        if form.is_valid():
            form.save()
            messages.success(request, "Remuneración registrada exitosamente.")
            return redirect('remuneraciones_list', condominio_id=condominio.id_condominio)
    else:
        form = RemuneracionForm(condominio_id=condominio_id)

    contexto = {
        'condominio': condominio,
        'form': form
    }
    return render(request, 'core/remuneracion_form.html', contexto)

# --- FIN: Vistas de RRHH ---
