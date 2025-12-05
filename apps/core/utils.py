# apps/core/utils.py
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML

def render_to_pdf(template_src, context_dict={}):
    """
    Renderiza una plantilla Django a un PDF usando WeasyPrint.
    """
    template = get_template(template_src)
    html_string = template.render(context_dict)

    # WeasyPrint espera una URL base para resolver rutas relativas (CSS, imágenes)
    # En este caso, como no tenemos rutas complejas, podemos omitirlo o usar un valor dummy.
    # Si tuviéramos archivos estáticos:
    # from django.contrib.staticfiles import finders
    # base_url = finders.find('css/style.css') # o cualquier archivo estático

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    # Opcional: Forzar la descarga del archivo
    # response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'

    return response
