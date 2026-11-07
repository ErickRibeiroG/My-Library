from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

SENHA = 'senha-forte-123'


class CadastroTests(TestCase):

    def dados(self, **extra):
        dados = {
            'first_name': 'Ana', 'last_name': 'Silva', 'email': 'Ana@Exemplo.com',
            'password1': SENHA, 'password2': SENHA,
        }
        dados.update(extra)
        return dados

    def test_cadastro_cria_usuario_e_faz_login(self):
        resposta = self.client.post(reverse('account:cadastro'), self.dados())
        self.assertRedirects(resposta, reverse('core:buscar'))
        usuario = User.objects.get()
        self.assertEqual(usuario.username, 'ana@exemplo.com')
        self.assertEqual(usuario.email, 'ana@exemplo.com')
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)

    def test_email_duplicado_e_recusado(self):
        User.objects.create_user(username='ana@exemplo.com', email='ana@exemplo.com', password=SENHA)
        resposta = self.client.post(reverse('account:cadastro'), self.dados())
        self.assertContains(resposta, 'Já existe uma conta com este e-mail')
        self.assertEqual(User.objects.count(), 1)

    def test_senhas_diferentes(self):
        resposta = self.client.post(reverse('account:cadastro'), self.dados(password2='outra-coisa-456'))
        self.assertContains(resposta, 'As senhas não coincidem')
        self.assertFalse(User.objects.exists())

    def test_senha_fraca(self):
        resposta = self.client.post(reverse('account:cadastro'), self.dados(password1='123', password2='123'))
        self.assertEqual(resposta.status_code, 200)
        self.assertFalse(User.objects.exists())


class LoginTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='Leitor', email='leitor@exemplo.com', password=SENHA, first_name='Léo'
        )

    def test_login_por_email_sem_diferenciar_maiusculas(self):
        resposta = self.client.post(reverse('account:login'), {'username': 'LEITOR@exemplo.com', 'password': SENHA})
        self.assertRedirects(resposta, reverse('core:home'))

    def test_login_por_nome_de_usuario(self):
        resposta = self.client.post(reverse('account:login'), {'username': 'leitor', 'password': SENHA})
        self.assertRedirects(resposta, reverse('core:home'))

    def test_login_com_emails_repetidos_escolhe_a_conta_certa(self):
        outro = User.objects.create_user(username='outro', email='leitor@exemplo.com', password='outra-senha-789')
        self.client.post(reverse('account:login'), {'username': 'leitor@exemplo.com', 'password': 'outra-senha-789'})
        self.assertEqual(int(self.client.session['_auth_user_id']), outro.pk)

    def test_senha_errada(self):
        resposta = self.client.post(reverse('account:login'), {'username': 'leitor@exemplo.com', 'password': 'errada'})
        self.assertContains(resposta, 'E-mail ou senha inválidos')

    def test_respeita_next(self):
        resposta = self.client.post(
            reverse('account:login') + '?next=/home/buscar/',
            {'username': 'leitor', 'password': SENHA, 'next': '/home/buscar/'},
        )
        self.assertRedirects(resposta, '/home/buscar/')

    def test_usuario_logado_e_redirecionado(self):
        self.client.force_login(self.usuario)
        self.assertRedirects(self.client.get(reverse('account:login')), reverse('core:home'))
        self.assertRedirects(self.client.get(reverse('account:cadastro')), reverse('core:home'))

    def test_logout(self):
        self.client.force_login(self.usuario)
        resposta = self.client.post(reverse('account:logout'))
        self.assertRedirects(resposta, reverse('account:login'))
        self.assertNotIn('_auth_user_id', self.client.session)


class PerfilTests(TestCase):

    def setUp(self):
        self.usuario = User.objects.create_user(
            username='ana@exemplo.com', email='ana@exemplo.com', password=SENHA, first_name='Ana'
        )
        self.client.force_login(self.usuario)

    def test_atualizar_dados_sincroniza_username(self):
        self.client.post(reverse('account:perfil'), {
            'acao': 'perfil', 'first_name': 'Ana Maria', 'last_name': 'Souza', 'email': 'nova@exemplo.com',
        })
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.first_name, 'Ana Maria')
        self.assertEqual(self.usuario.username, 'nova@exemplo.com')

    def test_email_de_outra_conta_e_recusado(self):
        User.objects.create_user(username='b@exemplo.com', email='b@exemplo.com', password=SENHA)
        resposta = self.client.post(reverse('account:perfil'), {
            'acao': 'perfil', 'first_name': 'Ana', 'last_name': '', 'email': 'B@exemplo.com',
        })
        self.assertContains(resposta, 'Já existe outra conta com este e-mail')

    def test_alterar_senha_mantem_sessao(self):
        resposta = self.client.post(reverse('account:perfil'), {
            'acao': 'senha', 'old_password': SENHA,
            'new_password1': 'nova-senha-456', 'new_password2': 'nova-senha-456',
        })
        self.assertRedirects(resposta, reverse('account:perfil'))
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password('nova-senha-456'))
        self.assertEqual(self.client.get(reverse('core:home')).status_code, 200)
