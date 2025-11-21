from django.test import TestCase
from decimal import Decimal
from django.utils import timezone
from apps.core.models import Condominio, Grupo, Unidad, CatMetodoPago, Pago
from apps.core.services import registrar_pago

class RegistrarPagoTests(TestCase):
    def setUp(self):
        self.condominio = Condominio.objects.create(nombre="Test Condo", rut_base=12345678, rut_dv="9")
        self.grupo = Grupo.objects.create(id_condominio=self.condominio, nombre="Torre A", tipo="Torre")
        self.unidad = Unidad.objects.create(id_grupo=self.grupo, codigo="101", coef_prop=1.0)
        self.metodo = CatMetodoPago.objects.create(codigo="TRANSFERENCIA", nombre="Transferencia")

    def test_registrar_pago_negativo_should_fail(self):
        """
        Prueba que NO debería permitir pagos negativos.
        Fallará si el bug existe (es decir, si NO lanza ValueError).
        """
        monto = Decimal("-5000")
        with self.assertRaises(ValueError):
            registrar_pago(
                unidad=self.unidad,
                monto=monto,
                metodo_pago=self.metodo,
                fecha_pago=timezone.now(),
                observacion="Pago negativo"
            )

    def test_registrar_pago_positivo_success(self):
        """
        Prueba que permite pagos positivos correctamente.
        """
        monto = Decimal("5000")
        pago = registrar_pago(
            unidad=self.unidad,
            monto=monto,
            metodo_pago=self.metodo,
            fecha_pago=timezone.now(),
            observacion="Pago positivo"
        )
        self.assertIsNotNone(pago.pk)
        self.assertEqual(pago.monto, monto)
        self.assertEqual(pago.tipo, Pago.TipoPago.NORMAL)
