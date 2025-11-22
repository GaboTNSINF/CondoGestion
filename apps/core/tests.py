from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from apps.core.models import Condominio, GastoCategoria, Proveedor, CatDocTipo, Gasto
from apps.usuarios.models import Usuario
from apps.core.forms import GastoForm
from apps.core.services import crear_gasto

class GastoFormValidationTests(TestCase):
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

    def test_gasto_uniqueness_validation(self):
        """
        Test that duplicate folio for same provider is rejected.
        """
        # Create first gasto
        Gasto.objects.create(
            id_condominio=self.condominio,
            id_gasto_categ=self.categoria,
            id_proveedor=self.proveedor,
            id_doc_tipo=self.doc_tipo,
            documento_folio='FOLIO-001',
            fecha_emision=timezone.now().date(),
            neto=100, iva=19, total=119,
            periodo='202501'
        )

        # Try to create duplicate via Form
        form_data = {
            'id_gasto_categ': self.categoria.pk,
            'id_proveedor': self.proveedor.pk,
            'id_doc_tipo': self.doc_tipo.pk,
            'documento_folio': 'FOLIO-001', # DUPLICATE
            'fecha_emision': timezone.now().date(),
            'fecha_venc': timezone.now().date(),
            'monto_total': 1190,
            'descripcion': 'Duplicate'
        }
        form = GastoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("Este folio ya fue registrado para este proveedor.", form.non_field_errors())

    def test_gasto_date_validation(self):
        """
        Test that fecha_venc cannot be before fecha_emision.
        """
        form_data = {
            'id_gasto_categ': self.categoria.pk,
            'id_proveedor': self.proveedor.pk,
            'id_doc_tipo': self.doc_tipo.pk,
            'documento_folio': 'FOLIO-002',
            'fecha_emision': timezone.now().date(),
            'fecha_venc': timezone.now().date() - timezone.timedelta(days=1), # INVALID
            'monto_total': 1190,
            'descripcion': 'Bad Dates'
        }
        form = GastoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_venc", form.errors)

    def test_gasto_calculation_logic(self):
        """
        Test that Neto/IVA are calculated correctly from Total.
        """
        total = Decimal('1190')
        expected_neto = Decimal('1000') # 1190 / 1.19
        expected_iva = Decimal('190')   # 1190 - 1000

        form_data = {
            'id_gasto_categ': self.categoria.pk,
            'id_proveedor': self.proveedor.pk,
            'id_doc_tipo': self.doc_tipo.pk,
            'documento_folio': 'FOLIO-CALC',
            'fecha_emision': timezone.now().date(),
            'fecha_venc': timezone.now().date(),
            'monto_total': total,
            'descripcion': 'Calc Test'
        }
        form = GastoForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

        gasto = crear_gasto(self.condominio, form, self.user)

        # Check calculation with reasonable precision (2 places)
        self.assertAlmostEqual(gasto.neto, expected_neto, places=2)
        self.assertAlmostEqual(gasto.iva, expected_iva, places=2)
        self.assertAlmostEqual(gasto.total, total, places=2)
        self.assertEqual(gasto.estado_validacion, Gasto.EstadoValidacion.PENDIENTE)
