from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from .models import CodigoVerificacion

Usuario = get_user_model()

class PerfilUpdateTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='password123',
            rut_base=12345678,
            rut_dv='9',
            nombres='Juan',
            apellidos='Perez'
        )
        self.client.force_login(self.user)

    def test_profile_update_triggers_2fa(self):
        """
        Test that changing the name triggers 2FA flow.
        """
        response = self.client.post(reverse('user_profile'), {
            'nombres': 'Juan Updated',
            'apellidos': 'Perez',
            'email': 'test@example.com'
        })

        # Should redirect to verify_otp
        self.assertRedirects(response, reverse('verify_otp'))

        # Check that OTP was generated
        otp = CodigoVerificacion.objects.filter(usuario=self.user, accion='perfil_update').first()
        self.assertIsNotNone(otp)

        # Check session has pending data
        session = self.client.session
        self.assertIn('pending_profile_update', session)
        self.assertEqual(session['pending_profile_update']['nombres'], 'Juan Updated')

    def test_password_update_triggers_2fa(self):
        """
        Test that changing password triggers 2FA flow (New Requirement).
        """
        response = self.client.post(reverse('user_profile'), {
            'change_password': '1',
            'old_password': 'password123',
            'new_password1': 'newpassword123',
            'new_password2': 'newpassword123',
        })

        # REQUIRED BEHAVIOR: Redirect to verify_otp
        self.assertRedirects(response, reverse('verify_otp'))

        # Check OTP generated
        otp = CodigoVerificacion.objects.filter(usuario=self.user, accion='password_update').first()
        self.assertIsNotNone(otp)

        # Check session
        session = self.client.session
        self.assertIn('pending_password_update', session)
        self.assertEqual(session['pending_password_update'], 'newpassword123')

    def test_no_change_does_not_trigger_2fa(self):
        """
        Submitting same data should not trigger 2FA.
        """
        response = self.client.post(reverse('user_profile'), {
            'nombres': 'Juan',
            'apellidos': 'Perez',
            'email': 'test@example.com'
        })

        # Should stay on profile page with message
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se detectaron cambios")

        # No OTP generated
        otp = CodigoVerificacion.objects.filter(usuario=self.user, accion='perfil_update').count()
        self.assertEqual(otp, 0)
