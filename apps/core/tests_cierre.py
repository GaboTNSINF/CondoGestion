# apps/core/tests_cierre.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from apps.core.models import Condominio, Unidad, Grupo, ProrrateoRegla, CatConceptoCargo, CatCobroEstado
from apps.core.services import generar_cierre_mensual

Usuario = get_user_model()

class CierreMensualServiceTest(TestCase):
    def setUp(self):
        self.condominio = Condominio.objects.create(nombre="Condominio de Prueba")

    def test_generar_cierre_sin_unidades_lanza_error(self):
        """
        Verifica que generar_cierre_mensual lanza ValueError si no hay unidades.
        """
        with self.assertRaisesRegex(ValueError, "No se generó ningún cobro"):
            generar_cierre_mensual(self.condominio, "202512")

class CierreMensualViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = Usuario.objects.create_superuser(
            email="admin@test.com",
            password="password",
            rut_base=1,
            rut_dv='9',
            nombres='Admin',
            apellidos='User'
        )
        self.client.login(email="admin@test.com", password="password")

        self.condominio = Condominio.objects.create(nombre="Condominio PDF")
        self.grupo = Grupo.objects.create(id_condominio=self.condominio, nombre="Torre A", tipo="Torre")
        self.unidad = Unidad.objects.create(
            id_grupo=self.grupo,
            codigo="101",
            coef_prop=Decimal("0.05")
        )
        # Pre-generar un cierre para que el PDF se pueda exportar
        concepto_gc, _ = CatConceptoCargo.objects.get_or_create(codigo='GASTO_COMUN', nombre='Gasto Común')
        ProrrateoRegla.objects.create(
            id_condominio=self.condominio,
            id_concepto_cargo=concepto_gc,
            criterio=ProrrateoRegla.CriterioProrrateo.COEF_PROP,
            vigente_desde="2023-01-01"
        )
        CatCobroEstado.objects.get_or_create(codigo='PENDIENTE')
        generar_cierre_mensual(self.condominio, "202512")


    def test_exportar_pdf_retorna_respuesta_correcta(self):
        """
        Verifica que la vista retorna un PDF cuando se solicita.
        """
        url = reverse('cierre_mensual', kwargs={'condominio_id': self.condominio.pk})
        response = self.client.get(url, {'export_pdf': 'true', 'periodo': '202512'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
