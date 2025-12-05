from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from weasyprint import HTML

def render_to_pdf(template_src, context_dict={}):
    """
    Renderiza un template de Django a PDF usando WeasyPrint.
    """
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()

    # Generate PDF
    # base_url is needed for relative paths (e.g. images, css)
    # For this snippet we assume external resources are absolute or handled via context.
    # In Django usually request.build_absolute_uri() is used but here we simplify.
    pdf = HTML(string=html).write_pdf(result)

    return HttpResponse(result.getvalue(), content_type='application/pdf')
