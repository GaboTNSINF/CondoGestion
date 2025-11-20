# apps/core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum

# --- IMPORTANTE: Importamos los modelos para poder buscar datos ---
from .models import Condominio, Gasto, Cobro
from .forms import GastoForm
from .services import generar_cierre_mensual

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
            # No guardamos inmediatamente para asignar el condominio
            gasto = form.save(commit=False)
            gasto.id_condominio = condominio
            gasto.save()
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
