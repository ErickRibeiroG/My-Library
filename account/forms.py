from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Q

User = get_user_model()


def _email_em_uso(email, exceto=None):
    usuarios = User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email))
    if exceto is not None:
        usuarios = usuarios.exclude(pk=exceto.pk)
    return usuarios.exists()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='E-mail ou usuário',
        max_length=254,
        widget=forms.TextInput(attrs={'autofocus': True, 'autocomplete': 'username', 'placeholder': 'voce@exemplo.com'}),
    )
    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'placeholder': '••••••••'}),
    )

    error_messages = {
        'invalid_login': 'E-mail ou senha inválidos.',
        'inactive': 'Esta conta está desativada.',
    }


class CadastroForm(forms.Form):
    first_name = forms.CharField(
        label='Nome',
        max_length=150,
        widget=forms.TextInput(attrs={'autocomplete': 'given-name', 'placeholder': 'Seu nome', 'autofocus': True}),
    )
    last_name = forms.CharField(
        label='Sobrenome',
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'autocomplete': 'family-name', 'placeholder': 'Seu sobrenome'}),
    )
    email = forms.EmailField(
        label='E-mail',
        max_length=150,
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'placeholder': 'voce@exemplo.com'}),
    )
    password1 = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Mínimo de 8 caracteres'}),
        help_text='Use pelo menos 8 caracteres, misturando letras e números.',
    )
    password2 = forms.CharField(
        label='Confirme a senha',
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Repita a senha'}),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if _email_em_uso(email):
            raise forms.ValidationError('Já existe uma conta com este e-mail.')
        return email

    def clean(self):
        dados = super().clean()
        senha, confirmacao = dados.get('password1'), dados.get('password2')

        if senha and confirmacao and senha != confirmacao:
            self.add_error('password2', 'As senhas não coincidem.')
        elif senha:
            usuario_temporario = User(
                username=dados.get('email', ''),
                email=dados.get('email', ''),
                first_name=dados.get('first_name', ''),
                last_name=dados.get('last_name', ''),
            )
            try:
                password_validation.validate_password(senha, usuario_temporario)
            except forms.ValidationError as erro:
                self.add_error('password1', erro)
        return dados

    def save(self):
        dados = self.cleaned_data
        return User.objects.create_user(
            username=dados['email'],
            email=dados['email'],
            password=dados['password1'],
            first_name=dados['first_name'].strip(),
            last_name=dados.get('last_name', '').strip(),
        )


class PerfilForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Nome', 'last_name': 'Sobrenome', 'email': 'E-mail'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['email'].required = True
        self._email_original = self.instance.email

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if _email_em_uso(email, exceto=self.instance):
            raise forms.ValidationError('Já existe outra conta com este e-mail.')
        return email

    def save(self, commit=True):
        usuario = super().save(commit=False)
        # Contas criadas pelo cadastro usam o e-mail como nome de usuário: mantém os dois em sincronia.
        if self._email_original and usuario.username.lower() == self._email_original.lower():
            usuario.username = usuario.email
        if commit:
            usuario.save()
        return usuario


class AlterarSenhaForm(PasswordChangeForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].label = 'Senha atual'
        self.fields['new_password1'].label = 'Nova senha'
        self.fields['new_password2'].label = 'Confirme a nova senha'
        self.fields['old_password'].widget.attrs.pop('autofocus', None)
        self.fields['new_password1'].help_text = 'Use pelo menos 8 caracteres, misturando letras e números.'
