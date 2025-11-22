from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def es_admin(user):
    return user.is_authenticated and user.tipo_usuario in ['super_admin', 'admin']

def solo_admin(view_func=None, redirect_to_portal=False):
    """
    Decorador para restringir el acceso solo a administradores.
    Si redirect_to_portal es True, redirige al portal de residentes en lugar de 403.
    """
    if view_func is None:
        return lambda u: solo_admin(u, redirect_to_portal=redirect_to_portal)

    def check_user(user):
        if es_admin(user):
            return True
        if redirect_to_portal:
            # Si queremos redirigir en vez de bloquear (útil para login o index si se comparte URL)
            return False
        # Por defecto, comportamiento estricto: Bloquear
        raise PermissionDenied

    decorator = user_passes_test(check_user, login_url='portal_residente' if redirect_to_portal else None)
    return decorator(view_func)

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin para vistas basadas en clases.
    """
    def test_func(self):
        return es_admin(self.request.user)

    def handle_no_permission(self):
        # Opción: Redirigir o 403
        # Aquí lanzamos 403 para ser estrictos como pide el usuario ("rechace la entrada")
        raise PermissionDenied
