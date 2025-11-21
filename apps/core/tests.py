from django.test import TestCase
from django.utils import timezone
from apps.core.models import Condominio, GastoCategoria, Proveedor, CatDocTipo, Gasto
from apps.usuarios.models import Usuario
from apps.core.forms import GastoForm
from apps.core.services import crear_gasto

class GastoAutoCalculationTests(TestCase):
    def setUp(self):
        self.condominio = Condominio.objects.create(nombre="Test Condo", rut_base=1, rut_dv="9")
        self.categoria = GastoCategoria.objects.create(nombre="Mantención")
        self.proveedor = Proveedor.objects.create(
            rut_base=12345678, rut_dv="K", nombre="Prov", tipo=Proveedor.TipoProveedor.EMPRESA
        )
        self.doc_tipo = CatDocTipo.objects.create(codigo="FACTURA", nombre="Factura")
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='password',
            rut_base=12345678,
            rut_dv='9',
            nombres='Test',
            apellidos='User'
        )

    def test_gasto_period_autocalculation(self):
        """
        Test that periodo is automatically calculated from fecha_emision.
        """
        fecha = timezone.datetime(2025, 11, 15).date() # 15/11/2025
        expected_periodo = "202511"

        form_data = {
            # 'periodo': ... not provided
            'id_gasto_categ': self.categoria.pk,
            'id_proveedor': self.proveedor.pk,
            'id_doc_tipo': self.doc_tipo.pk,
            'documento_folio': '123',
            'fecha_emision': fecha,
            'neto': 1000,
            'iva': 190,
            'descripcion': 'Test Gasto Auto Period'
        }
        form = GastoForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

        # Create gasto via service
        gasto = crear_gasto(self.condominio, form, self.user)

        self.assertEqual(gasto.periodo, expected_periodo)

    def test_form_defaults_to_today(self):
        """
        Verify that GastoForm defaults dates to today.
        """
        form = GastoForm()
        self.assertEqual(form.initial['fecha_emision'], timezone.now().date())
        self.assertEqual(form.initial['fecha_venc'], timezone.now().date())
