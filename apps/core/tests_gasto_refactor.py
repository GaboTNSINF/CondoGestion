from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from apps.core.models import Proveedor, GastoCategoria
from apps.core.views import proveedor_create_ajax, categoria_create_ajax
from apps.usuarios.models import Usuario
import json

class AjaxCreationTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='password',
            rut_base=12345678,
            rut_dv='9',
            nombres='Test',
            apellidos='User'
        )

    def test_proveedor_create_ajax(self):
        data = {
            'name': 'New Provider',
            'rut': 11111111,
            'dv': '1'
        }
        request = self.factory.post(
            reverse('proveedor_create_ajax'),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.user

        response = proveedor_create_ajax(request)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertTrue(Proveedor.objects.filter(rut_base=11111111).exists())

    def test_categoria_create_ajax(self):
        data = {
            'name': 'New Category'
        }
        request = self.factory.post(
            reverse('categoria_create_ajax'),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.user

        response = categoria_create_ajax(request)
        self.assertEqual(response.status_code, 200)

        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertTrue(GastoCategoria.objects.filter(nombre='New Category').exists())
