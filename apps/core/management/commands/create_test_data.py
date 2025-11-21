from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario
from apps.core.models import Condominio

class Command(BaseCommand):
    help = 'Crea datos de prueba para verificar el dashboard'

    def handle(self, *args, **kwargs):
        # Crear usuario de prueba
        if not Usuario.objects.filter(email='test@example.com').exists():
            usuario = Usuario.objects.create_user(
                email='test@example.com',
                password='password123',
                rut_base=12345678,
                rut_dv='9',
                nombres='Juan',
                apellidos='Pérez'
            )
            self.stdout.write(self.style.SUCCESS('Usuario creado: test@example.com / password123'))
        else:
            self.stdout.write(self.style.WARNING('El usuario test@example.com ya existe'))

        # Crear condominio de prueba
        if not Condominio.objects.filter(nombre='Condominio Los Andes').exists():
            condominio = Condominio.objects.create(
                nombre='Condominio Los Andes',
                rut_base=76543210,
                rut_dv='K',
                direccion='Av. Libertador 1234',
                comuna='Santiago',
                region='RM'
            )
            self.stdout.write(self.style.SUCCESS('Condominio creado: Condominio Los Andes'))
        else:
            self.stdout.write(self.style.WARNING('El condominio Los Andes ya existe'))
