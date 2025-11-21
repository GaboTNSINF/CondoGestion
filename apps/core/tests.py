from django.test import TestCase
from django.utils import timezone
from apps.core.models import Condominio, GastoCategoria, Proveedor, CatDocTipo
from apps.core.forms import GastoForm

class GastoFormValidationTests(TestCase):
    def setUp(self):
        self.condominio = Condominio.objects.create(nombre="Test Condo", rut_base=1, rut_dv="9")
        self.categoria = GastoCategoria.objects.create(nombre="Mantención")
        self.proveedor = Proveedor.objects.create(
            rut_base=12345678, rut_dv="K", nombre="Prov", tipo=Proveedor.TipoProveedor.EMPRESA
        )
        self.doc_tipo = CatDocTipo.objects.create(codigo="FACTURA", nombre="Factura")

    def test_periodo_invalid_format_rejected(self):
        """
        Test that GastoForm rejects invalid format (alphanumeric).
        """
        form_data = {
            'periodo': '2023A1', # Invalid format (alphanumeric), length 6
            'id_gasto_categ': self.categoria.pk,
            'id_proveedor': self.proveedor.pk,
            'id_doc_tipo': self.doc_tipo.pk,
            'documento_folio': '123',
            'fecha_emision': timezone.now().date(),
            'neto': 1000,
            'iva': 190,
            'descripcion': 'Test Gasto'
        }
        form = GastoForm(data=form_data)
        # This assertion should PASS if the fix works (form IS INVALID)
        self.assertFalse(form.is_valid(), "Form should be invalid for '2023A1'")
        self.assertIn("El periodo debe contener solo números.", form.errors['periodo'])

    def test_periodo_valid_format(self):
        """
        Test that valid YYYYMM format is accepted.
        """
        form_data = {
            'periodo': '202301',
            'id_gasto_categ': self.categoria.pk,
            'id_proveedor': self.proveedor.pk,
            'id_doc_tipo': self.doc_tipo.pk,
            'documento_folio': '123',
            'fecha_emision': timezone.now().date(),
            'neto': 1000,
            'iva': 190,
            'descripcion': 'Test Gasto Valid'
        }
        form = GastoForm(data=form_data)
        self.assertTrue(form.is_valid())
