from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from apps.core.models import (
    Condominio, Grupo, Unidad, CatViviendaSubtipo, CondominioAnexoRegla,
    Gasto, GastoCategoria, CatConceptoCargo, Cobro, CobroDetalle, ParamReglamento
)
from apps.core.services import generar_cierre_mensual

class CierreMensualIdempotencyTests(TestCase):
    def setUp(self):
        self.condominio = Condominio.objects.create(nombre="Test Condo", rut_base=11111111, rut_dv="1")
        self.grupo = Grupo.objects.create(id_condominio=self.condominio, nombre="Torre A", tipo="Torre")
        self.subtipo = CatViviendaSubtipo.objects.create(codigo="1D1B", nombre="1 Dorm 1 Baño")

        # Unidad cobrable con anexo
        self.unidad = Unidad.objects.create(
            id_grupo=self.grupo,
            codigo="101",
            coef_prop=1.0,
            id_viv_subtipo=self.subtipo,
            anexo_cobrable=True
        )

        # Setup ParamReglamento to avoid float/decimal crash in services.py default handling
        ParamReglamento.objects.create(
            id_condominio=self.condominio,
            recargo_fondo_reserva_pct=Decimal('5.00')
        )

        # Regla de Anexo
        CondominioAnexoRegla.objects.create(
            id_condominio=self.condominio,
            id_viv_subtipo=self.subtipo,
            anexo_tipo=CondominioAnexoRegla.AnexoTipo.ESTACIONAMIENTO,
            incluido_qty=0,
            cobrable_por_sobre_qty=1,
            vigente_desde=timezone.now().date()
        )

        # Gasto para que haya cierre
        categoria = GastoCategoria.objects.create(nombre="Mantención")
        Gasto.objects.create(
            id_condominio=self.condominio,
            periodo='202401',
            id_gasto_categ=categoria,
            neto=100000,
            iva=19000,
            fecha_emision=timezone.now()
        )

    def test_anexo_charges_duplication_bug(self):
        """
        Verifica que al correr el cierre mensual dos veces, no se dupliquen los cobros de anexos.
        """
        periodo = '202401'

        # Primera ejecución
        generar_cierre_mensual(self.condominio, periodo)

        cobro = Cobro.objects.get(id_unidad=self.unidad, periodo=periodo)
        # Debería tener 2 detalles: 1 Gasto Común (Prorrateo) + 1 Cargo Anexo
        detalles_count_run1 = CobroDetalle.objects.filter(id_cobro=cobro).count()
        self.assertEqual(detalles_count_run1, 2, "Debe haber 2 detalles en la primera ejecución")

        # Segunda ejecución (Simula re-calculo)
        generar_cierre_mensual(self.condominio, periodo)

        cobro.refresh_from_db()
        detalles_count_run2 = CobroDetalle.objects.filter(id_cobro=cobro).count()

        # Si el bug existe, esto fallará (serán 3)
        self.assertEqual(detalles_count_run2, 2, f"Debe mantenerse en 2 detalles tras re-ejecución, pero encontró {detalles_count_run2}")
