from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from account.forms import AlterarSenhaForm, CadastroForm, LoginForm, PerfilForm


class LoginView(auth_views.LoginView):
    template_name = 'account/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


login = LoginView.as_view()
sair = auth_views.LogoutView.as_view()


def cadastro(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    form = CadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        auth_login(request, usuario, backend='account.backends.EmailOuUsuarioBackend')
        messages.success(request, f'Bem-vindo(a), {usuario.first_name}! Comece buscando um livro.')
        return redirect('core:buscar')

    return render(request, 'account/cadastro.html', {'form': form})


@login_required
def perfil(request):
    acao = request.POST.get('acao') if request.method == 'POST' else None

    form_perfil = PerfilForm(request.POST if acao == 'perfil' else None, instance=request.user)
    form_senha = AlterarSenhaForm(request.user, request.POST if acao == 'senha' else None)

    if acao == 'perfil' and form_perfil.is_valid():
        form_perfil.save()
        messages.success(request, 'Seus dados foram atualizados.')
        return redirect('account:perfil')

    if acao == 'senha' and form_senha.is_valid():
        usuario = form_senha.save()
        update_session_auth_hash(request, usuario)
        messages.success(request, 'Sua senha foi alterada.')
        return redirect('account:perfil')

    return render(request, 'account/perfil.html', {
        'form_perfil': form_perfil,
        'form_senha': form_senha,
    })
