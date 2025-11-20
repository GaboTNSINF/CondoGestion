# apps/core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse

# --- IMPORTANTE: Importamos los modelos para poder buscar datos ---
from .models import Condominio, Gasto
from .forms import GastoForm

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
