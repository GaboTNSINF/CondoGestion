from django import forms
from .models import Gasto

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = [
            'periodo',
            'id_gasto_categ',
            'id_proveedor',
            'id_doc_tipo',
            'documento_folio',
            'fecha_emision',
            'fecha_venc',
            'neto',
            'iva',
            'descripcion',
            'evidencia_url'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_venc': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'periodo': forms.TextInput(attrs={'placeholder': 'YYYYMM', 'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'neto': forms.NumberInput(attrs={'class': 'form-control'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control'}),
            'documento_folio': forms.TextInput(attrs={'class': 'form-control'}),
            'evidencia_url': forms.URLInput(attrs={'class': 'form-control'}),
            'id_gasto_categ': forms.Select(attrs={'class': 'form-control'}),
            'id_proveedor': forms.Select(attrs={'class': 'form-control'}),
            'id_doc_tipo': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'id_gasto_categ': 'Categoría',
            'id_proveedor': 'Proveedor',
            'id_doc_tipo': 'Tipo de Documento',
            'documento_folio': 'Folio Documento',
            'evidencia_url': 'URL Evidencia (opcional)',
        }
