from django import forms
from .models import Usuario

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'email']
        widgets = {
            'nombres': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control form-control-lg'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-lg'}),
        }

class OTPVerificationForm(forms.Form):
    codigo = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '123456',
            'autocomplete': 'off',
            'pattern': '[0-9]*',
            'inputmode': 'numeric'
        }),
        label="Código de Verificación"
    )
