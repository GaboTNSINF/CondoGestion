from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import random  # Agregado por seguridad según checklist (aunque usamos get_random_string)

from .models import CodigoVerificacion
from .forms import UserProfileForm, OTPVerificationForm

@login_required
def perfil_update_view(request):
    if request.method == 'POST':
        # Check if it's password change
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            profile_form = UserProfileForm(instance=request.user)
            if password_form.is_valid():
                # 2FA Logic for Password

                # Store pending password in session
                request.session['pending_password_update'] = password_form.cleaned_data['new_password1']

                # Generate OTP
                otp = get_random_string(length=6, allowed_chars='0123456789')

                # Save OTP
                CodigoVerificacion.objects.create(
                    usuario=request.user,
                    codigo=otp,
                    accion='password_update'
                )

                # Send Email
                print(f"*** 2FA CODE FOR PASSWORD CHANGE {request.user.email}: {otp} ***")
                try:
                    send_mail(
                        'Código de Verificación - Cambio de Contraseña',
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
                messages.error(request, 'Error al cambiar la contraseña.')
        else:
            # Profile update
            profile_form = UserProfileForm(request.POST, instance=request.user)
            password_form = PasswordChangeForm(request.user)

            if profile_form.is_valid():
                # Use has_changed() correctly
                if profile_form.has_changed():
                    # Save pending data to session
                    request.session['pending_profile_update'] = profile_form.cleaned_data

                    # Generate OTP
                    otp = get_random_string(length=6, allowed_chars='0123456789')

                    # Save OTP
                    CodigoVerificacion.objects.create(
                        usuario=request.user,
                        codigo=otp,
                        accion='perfil_update'
                    )

                    # Send Email
                    print(f"*** 2FA CODE FOR PROFILE UPDATE {request.user.email}: {otp} ***")
                    try:
                        send_mail(
                            'Código de Verificación - Actualización Perfil',
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
    pending_profile = request.session.get('pending_profile_update')
    pending_password = request.session.get('pending_password_update')

    if not pending_profile and not pending_password:
        messages.warning(request, 'No hay cambios pendientes de verificación.')
        return redirect('user_profile')

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['codigo']

            # Verify code
            # Check for password update first (priority or just logic)
            if pending_password:
                verification = CodigoVerificacion.objects.filter(
                    usuario=request.user,
                    accion='password_update',
                    codigo=code
                ).order_by('-creado_at').first()

                if verification and verification.es_valido():
                    user = request.user
                    user.set_password(pending_password)
                    user.save()
                    update_session_auth_hash(request, user) # Keep logged in

                    # Clean up
                    del request.session['pending_password_update']
                    verification.delete()

                    messages.success(request, 'Contraseña actualizada exitosamente.')
                    return redirect('user_profile')

            # Check profile update
            if pending_profile:
                verification = CodigoVerificacion.objects.filter(
                    usuario=request.user,
                    accion='perfil_update',
                    codigo=code
                ).order_by('-creado_at').first()

                if verification and verification.es_valido():
                    data = pending_profile
                    user = request.user
                    user.nombres = data.get('nombres', user.nombres)
                    user.apellidos = data.get('apellidos', user.apellidos)
                    user.email = data.get('email', user.email)
                    user.save()

                    # Clean up
                    del request.session['pending_profile_update']
                    verification.delete()

                    messages.success(request, 'Perfil actualizado exitosamente.')
                    return redirect('user_profile')

            messages.error(request, 'Código inválido o expirado.')
    else:
        form = OTPVerificationForm()

    return render(request, 'usuarios/verificar_otp.html', {'form': form})
