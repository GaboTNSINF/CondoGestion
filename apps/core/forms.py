from django import forms
from django.utils import timezone
from .models import Gasto, Pago, CatMetodoPago, Trabajador, Remuneracion

class GastoForm(forms.ModelForm):
    class Meta:
        model = Gasto
        fields = [
            # 'periodo',  <-- Removed from visible fields, auto-calculated
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
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'fecha_venc': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            # 'periodo': forms.TextInput(attrs={'placeholder': 'YYYYMM', 'class': 'form-control form-control-lg'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-lg'}),
            'neto': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'iva': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'documento_folio': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'evidencia_url': forms.URLInput(attrs={'class': 'form-control form-control-lg'}),
            'id_gasto_categ': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'id_proveedor': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'id_doc_tipo': forms.Select(attrs={'class': 'form-control form-control-lg'}),
        }
        labels = {
            'id_gasto_categ': 'Categoría',
            'id_proveedor': 'Proveedor',
            'id_doc_tipo': 'Tipo de Documento',
            'documento_folio': 'Folio Documento',
            'evidencia_url': 'URL Evidencia (opcional)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today
        today = timezone.now().date()
        if not self.instance.pk and 'fecha_emision' not in self.initial:
            self.initial['fecha_emision'] = today
        if not self.instance.pk and 'fecha_venc' not in self.initial:
            self.initial['fecha_venc'] = today

    # Removed clean_periodo as field is removed from form

class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ['id_unidad', 'monto', 'id_metodo_pago', 'fecha_pago', 'observacion']
        widgets = {
            'id_unidad': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control form-control-lg'}),
            'id_metodo_pago': forms.Select(attrs={'class': 'form-control form-control-lg'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'observacion': forms.Textarea(attrs={'rows': 2, 'class': 'form-control form-control-lg'}),
        }
        labels = {
            'id_unidad': 'Unidad',
            'id_metodo_pago': 'Método de Pago',
        }

    def __init__(self, *args, **kwargs):
        condominio_id = kwargs.pop('condominio_id', None)
        super().__init__(*args, **kwargs)

        # Default to today
        if not self.instance.pk and 'fecha_pago' not in self.initial:
            self.initial['fecha_pago'] = timezone.now().date()

        if condominio_id:
            # Filter units by condominio
            from .models import Unidad
            self.fields['id_unidad'].queryset = Unidad.objects.filter(id_grupo__id_condominio_id=condominio_id)

class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombres', 'apellidos', 'rut_base', 'rut_dv', 'cargo', 'email', 'telefono', 'tipo']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control'}),
            'rut_base': forms.NumberInput(attrs={'class': 'form-control'}),
            'rut_dv': forms.TextInput(attrs={'class': 'form-control', 'maxlength': '1'}),
            'cargo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'tipo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Planta, Reemplazo'}),
        }

class RemuneracionForm(forms.ModelForm):
    class Meta:
        model = Remuneracion
        fields = ['id_trabajador', 'periodo', 'tipo', 'bruto', 'imposiciones', 'descuentos', 'liquido', 'fecha_pago', 'id_metodo_pago', 'observacion']
        widgets = {
            'id_trabajador': forms.Select(attrs={'class': 'form-control'}),
            'periodo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'YYYYMM'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'bruto': forms.NumberInput(attrs={'class': 'form-control'}),
            'imposiciones': forms.NumberInput(attrs={'class': 'form-control'}),
            'descuentos': forms.NumberInput(attrs={'class': 'form-control'}),
            'liquido': forms.NumberInput(attrs={'class': 'form-control'}),
            'fecha_pago': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'id_metodo_pago': forms.Select(attrs={'class': 'form-control'}),
            'observacion': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        condominio_id = kwargs.pop('condominio_id', None)
        super().__init__(*args, **kwargs)
        if condominio_id:
             self.fields['id_trabajador'].queryset = Trabajador.objects.filter(id_condominio_id=condominio_id)
