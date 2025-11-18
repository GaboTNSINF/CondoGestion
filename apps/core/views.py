# apps/core/views.py
from django.shortcuts import render
# Importamos el decorador de seguridad
from django.contrib.auth.decorators import login_required

# --- INICIO: Vistas del Dashboard ---

@login_required  # <--- ¡SEGURIDAD POR DEFECTO!
def index_view(request):
    """
    Esta es la vista principal (Dashboard) de la aplicación.
    El decorador @login_required asegura que SOLO usuarios 
    autenticados puedan ver esto. Si no, los manda al login.
    """
    
    # Preparamos los datos que queremos enviar a la plantilla (frontend)
    contexto = {
        'usuario': request.user
    }
    
    # Renderizamos la plantilla 'index.html' (que crearemos en el sig. paso)
    return render(request, 'index.html', contexto)

# --- FIN: Vistas del Dashboard ---