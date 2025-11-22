from django import forms
from django.utils import timezone
from .models import Gasto, Pago, CatMetodoPago, Trabajador, Remuneracion

class GastoForm(forms.ModelForm):
    # Campo calculado para UX (reemplaza neto/iva)
    monto_total = forms.DecimalField(
        max_digits=12, decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-lg', 'placeholder': 'Monto Total (con IVA)'}),
        label='Monto Total',
        help_text='Monto final a pagar (con IVA incluido).'
    )

    class Meta:
        model = Gasto
        fields = [
            # 'periodo',  <-- Removed
            'id_gasto_categ',
            'id_proveedor',
            'id_doc_tipo',
            'documento_folio',
            'fecha_emision',
            'fecha_venc',
            # 'neto', <-- Removed
            # 'iva',  <-- Removed
            'descripcion',
            'evidencia_url'
        ]
        widgets = {
            'fecha_emision': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'fecha_venc': forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-lg'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'class': 'form-control form-control-lg'}),
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
        help_texts = {
            'documento_folio': 'Número único impreso en la boleta/factura.',
            'fecha_emision': 'Fecha de emisión del documento.',
            'fecha_venc': 'Fecha límite de pago.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date to today
        today = timezone.now().date()
        if not self.instance.pk and 'fecha_emision' not in self.initial:
            self.initial['fecha_emision'] = today
        if not self.instance.pk and 'fecha_venc' not in self.initial:
            self.initial['fecha_venc'] = today

        # Pre-fill monto_total if editing
        if self.instance.pk:
            self.initial['monto_total'] = self.instance.total

    def clean(self):
        cleaned_data = super().clean()
        proveedor = cleaned_data.get('id_proveedor')
        folio = cleaned_data.get('documento_folio')
        fecha_emision = cleaned_data.get('fecha_emision')
        fecha_venc = cleaned_data.get('fecha_venc')

        # A. Unicidad del Documento
        if proveedor and folio:
            # Check if exists (exclude self if editing)
            exists = Gasto.objects.filter(id_proveedor=proveedor, documento_folio=folio)
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                raise forms.ValidationError("Este folio ya fue registrado para este proveedor.")

        # B. Validación de Fechas
        if fecha_emision and fecha_venc:
            if fecha_venc < fecha_emision:
                self.add_error('fecha_venc', "La fecha de vencimiento no puede ser anterior a la emisión.")

        return cleaned_data

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
