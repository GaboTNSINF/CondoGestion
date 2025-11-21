from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

from .models import CodigoVerificacion
from .forms import UserProfileForm, OTPVerificationForm

@login_required
def user_profile_view(request):
    if request.method == 'POST':
        # Check if it's password change
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            profile_form = UserProfileForm(instance=request.user)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Contraseña actualizada exitosamente.')
                return redirect('user_profile')
            else:
                messages.error(request, 'Error al cambiar la contraseña.')
        else:
            # Profile update
            profile_form = UserProfileForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(request.user)

            if profile_form.is_valid():
                # 2FA Logic: Don't save yet
                # Check if any critical field changed
                changed_data = profile_form.cleaned_data
                if (changed_data['email'] != request.user.email or
                    changed_data['nombres'] != request.user.nombres or
                    changed_data['apellidos'] != request.user.apellidos):

                    # Save pending data to session
                    request.session['pending_profile_update'] = {
                        'nombres': changed_data['nombres'],
                        'apellidos': changed_data['apellidos'],
                        'email': changed_data['email']
                    }

                    # Generate OTP
                    otp = get_random_string(length=6, allowed_chars='0123456789')

                    # Save OTP
                    CodigoVerificacion.objects.create(
                        usuario=request.user,
                        codigo=otp,
                        accion='perfil_update'
                    )

                    # Send Email (Mock in dev usually, but using send_mail)
                    # In production this needs a backend. In dev console backend is default.
                    print(f"*** 2FA CODE FOR {request.user.email}: {otp} ***") # For debugging/demo
                    try:
                        send_mail(
                            'Código de Verificación - CondoGestión',
                            f'Tu código es: {otp}. Expira en 10 minutos.',
                            settings.DEFAULT_FROM_EMAIL or 'noreply@condogestion.cl',
                            [request.user.email],
                            fail_silently=True,
                        )
                    except Exception:
                        pass

                    messages.info(request, f'Se ha enviado un código de verificación a {request.user.email}.')
                    return redirect('verify_otp')
                else:
                    messages.info(request, 'No se detectaron cambios.')
    else:
        profile_form = UserProfileForm(instance=request.user)
        password_form = PasswordChangeForm(request.user)

    return render(request, 'usuarios/perfil.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })

@login_required
def verify_otp_view(request):
    if 'pending_profile_update' not in request.session:
        messages.warning(request, 'No hay cambios pendientes de verificación.')
        return redirect('user_profile')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['codigo']

            # Verify code
            # Get latest code for this action
            verification = CodigoVerificacion.objects.filter(
                usuario=request.user,
                accion='perfil_update',
                codigo=code
            ).order_by('-creado_at').first()

            if verification and verification.es_valido():
                # Apply changes
                data = request.session['pending_profile_update']
                user = request.user
                user.nombres = data['nombres']
                user.apellidos = data['apellidos']
                user.email = data['email']
                user.save()

                # Clean up
                del request.session['pending_profile_update']
                verification.delete() # Optional: prevent reuse

                messages.success(request, 'Perfil actualizado exitosamente.')
                return redirect('user_profile')
            else:
                messages.error(request, 'Código inválido o expirado.')
    else:
        form = OTPVerificationForm()

    return render(request, 'usuarios/verificar_otp.html', {'form': form})
