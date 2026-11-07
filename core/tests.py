from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import Livro
from core.services import buscar_livros
from core.services.base import LivroExterno, ResultadoBusca, extrair_ano, https
from core.services.googlebooks import GoogleBooks
from core.services.openlibrary import OpenLibrary

User = get_user_model()


def criar_usuario(email='ana@exemplo.com', senha='senha-forte-123', **extra):
    return User.objects.create_user(username=email, email=email, password=senha, first_name='Ana', **extra)


def resposta_json(dados, status=200):
    resposta = mock.Mock()
    resposta.status_code = status
    resposta.json.return_value = dados
    if status >= 400:
        resposta.raise_for_status.side_effect = requests.HTTPError(f'{status} Error')
    else:
        resposta.raise_for_status.return_value = None
    return resposta


GOOGLE_RESPOSTA = {
    'totalItems': 2,
    'items': [
        {
            'id': 'abc123',
            'volumeInfo': {
                'title': 'Duna',
                'authors': ['Frank Herbert'],
                'publishedDate': '2017-03-01',
                'pageCount': 680,
                'categories': ['Ficção'],
                'imageLinks': {'thumbnail': 'http://books.google.com/capa.jpg&edge=curl'},
                'description': '<p>Um <b>clássico</b>.</p>',
            },
        },
        {'id': 'semdados', 'volumeInfo': {'title': 'Sem dados'}},
    ],
}

OPENLIBRARY_RESPOSTA = {
    'numFound': 1,
    'docs': [{
        'key': '/works/OL1W',
        'title': 'Dom Casmurro',
        'author_name': ['Machado de Assis'],
        'first_publish_year': 1899,
        'cover_i': 42,
        'number_of_pages_median': 256,
        'subject': ['Accessible book', 'Romance brasileiro'],
    }],
}


# ==================== MODELO ====================

class LivroModelTests(TestCase):

    def setUp(self):
        self.usuario = criar_usuario()

    def test_definir_status_lido_registra_data(self):
        livro = Livro(usuario=self.usuario, titulo='X')
        livro.definir_status(Livro.Status.LIDO)
        self.assertEqual(livro.lido_em, timezone.localdate())

        livro.definir_status(Livro.Status.QUERO)
        self.assertIsNone(livro.lido_em)

    def test_link_externo(self):
        self.assertEqual(Livro(externo_id='gb:abc').link_externo, 'https://books.google.com/books?id=abc')
        self.assertEqual(Livro(externo_id='ol:OL1W').link_externo, 'https://openlibrary.org/works/OL1W')
        self.assertEqual(Livro(externo_id='').link_externo, '')

    def test_busca_no_queryset(self):
        Livro.objects.create(usuario=self.usuario, titulo='Duna', autor='Frank Herbert')
        Livro.objects.create(usuario=self.usuario, titulo='Outro', autor='Alguém')
        self.assertEqual(Livro.objects.buscar('herbert').count(), 1)
        self.assertEqual(Livro.objects.buscar('').count(), 2)


# ==================== ACESSO E ISOLAMENTO ====================

class AcessoTests(TestCase):

    def test_paginas_exigem_login(self):
        for nome in ('core:home', 'core:biblioteca', 'core:buscar'):
            resposta = self.client.get(reverse(nome))
            self.assertRedirects(resposta, f'{reverse("account:login")}?next={reverse(nome)}')

    def test_usuario_nao_ve_nem_altera_livros_de_outro(self):
        dono = criar_usuario('dono@exemplo.com')
        intruso = criar_usuario('intruso@exemplo.com')
        livro = Livro.objects.create(usuario=dono, titulo='Segredo')

        self.client.force_login(intruso)
        self.assertNotContains(self.client.get(reverse('core:home')), 'Segredo')
        self.assertEqual(self.client.get(reverse('core:detalhe', args=[livro.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('core:remover', args=[livro.pk])).status_code, 404)
        self.assertTrue(Livro.objects.filter(pk=livro.pk).exists())

    def test_acoes_so_aceitam_post(self):
        usuario = criar_usuario()
        livro = Livro.objects.create(usuario=usuario, titulo='X')
        self.client.force_login(usuario)
        self.assertEqual(self.client.get(reverse('core:remover', args=[livro.pk])).status_code, 405)


# ==================== VIEWS ====================

class ViewsTests(TestCase):

    def setUp(self):
        self.usuario = criar_usuario()
        self.client.force_login(self.usuario)

    def dados_livro(self, **extra):
        dados = {
            'externo_id': 'gb:abc', 'titulo': 'Duna', 'autor': 'Frank Herbert', 'ano': '2017',
            'paginas': '680', 'categoria': 'Ficção', 'capa': 'https://exemplo.com/c.jpg',
            'descricao': '', 'tipo': 'quero',
        }
        dados.update(extra)
        return dados

    def test_home_mostra_estatisticas(self):
        Livro.objects.create(usuario=self.usuario, titulo='A', tipo='lido', paginas=100, avaliacao=4)
        Livro.objects.create(usuario=self.usuario, titulo='B', tipo='lido', paginas=50, avaliacao=5)
        Livro.objects.create(usuario=self.usuario, titulo='C', tipo='quero')

        resposta = self.client.get(reverse('core:home'))
        resumo = resposta.context['resumo']
        self.assertEqual(resumo['total'], 3)
        self.assertEqual(resumo['lidos'], 2)
        self.assertEqual(resumo['paginas_lidas'], 150)
        self.assertEqual(resumo['percentual_lido'], 67)
        self.assertAlmostEqual(resumo['media_avaliacao'], 4.5)

    def test_home_vazia_mostra_boas_vindas(self):
        self.assertContains(self.client.get(reverse('core:home')), 'Sua biblioteca está vazia')

    def test_adicionar_livro(self):
        resposta = self.client.post(reverse('core:adicionar'), self.dados_livro(next='/home/buscar/?q=duna'))
        self.assertRedirects(resposta, '/home/buscar/?q=duna', fetch_redirect_response=False)
        livro = Livro.objects.get()
        self.assertEqual(livro.usuario, self.usuario)
        self.assertEqual(livro.paginas, 680)

    def test_adicionar_novamente_atualiza_status_sem_duplicar(self):
        self.client.post(reverse('core:adicionar'), self.dados_livro())
        self.client.post(reverse('core:adicionar'), self.dados_livro(tipo='lido'))
        livro = Livro.objects.get()
        self.assertEqual(livro.tipo, 'lido')
        self.assertIsNotNone(livro.lido_em)

    def test_adicionar_sem_paginas_nao_quebra(self):
        self.client.post(reverse('core:adicionar'), self.dados_livro(paginas=''))
        self.assertIsNone(Livro.objects.get().paginas)

    def test_adicionar_ignora_next_externo(self):
        resposta = self.client.post(reverse('core:adicionar'), self.dados_livro(next='https://malicioso.com/'))
        self.assertRedirects(resposta, reverse('core:buscar'), fetch_redirect_response=False)

    def test_adicionar_com_status_invalido(self):
        self.client.post(reverse('core:adicionar'), self.dados_livro(tipo='roubado'))
        self.assertFalse(Livro.objects.exists())

    def test_alterar_status(self):
        livro = Livro.objects.create(usuario=self.usuario, titulo='X')
        self.client.post(reverse('core:alterar_status', args=[livro.pk]), {'tipo': 'lido'})
        livro.refresh_from_db()
        self.assertEqual(livro.tipo, 'lido')

        self.client.post(reverse('core:alterar_status', args=[livro.pk]), {'tipo': 'inexistente'})
        livro.refresh_from_db()
        self.assertEqual(livro.tipo, 'lido')

    def test_avaliar_e_remover_avaliacao(self):
        livro = Livro.objects.create(usuario=self.usuario, titulo='X', tipo='lido')
        url = reverse('core:avaliar', args=[livro.pk])

        self.client.post(url, {'avaliacao': '4'})
        livro.refresh_from_db()
        self.assertEqual(livro.avaliacao, 4)

        self.client.post(url, {'avaliacao': '9'})
        livro.refresh_from_db()
        self.assertEqual(livro.avaliacao, 4)

        self.client.post(url, {'avaliacao': '0'})
        livro.refresh_from_db()
        self.assertIsNone(livro.avaliacao)

    def test_remover(self):
        livro = Livro.objects.create(usuario=self.usuario, titulo='X')
        self.client.post(reverse('core:remover', args=[livro.pk]))
        self.assertFalse(Livro.objects.exists())

    def test_biblioteca_filtra_e_ordena(self):
        Livro.objects.create(usuario=self.usuario, titulo='Banana', tipo='lido', avaliacao=3)
        Livro.objects.create(usuario=self.usuario, titulo='Abacaxi', tipo='lido', avaliacao=5)
        Livro.objects.create(usuario=self.usuario, titulo='Caju', tipo='quero')

        resposta = self.client.get(reverse('core:biblioteca'), {'status': 'lido', 'ordem': 'avaliacao'})
        titulos = [livro.titulo for livro in resposta.context['page_obj']]
        self.assertEqual(titulos, ['Abacaxi', 'Banana'])

        resposta = self.client.get(reverse('core:biblioteca'), {'q': 'caju'})
        self.assertEqual([l.titulo for l in resposta.context['page_obj']], ['Caju'])

    def test_detalhe(self):
        livro = Livro.objects.create(usuario=self.usuario, titulo='Duna', descricao='Areia.', tipo='lido')
        resposta = self.client.get(reverse('core:detalhe', args=[livro.pk]))
        self.assertContains(resposta, 'Areia.')
        self.assertContains(resposta, 'Sua avaliação')

    @mock.patch('core.views.buscar_livros')
    def test_buscar_marca_livros_ja_na_estante(self, buscar_mock):
        Livro.objects.create(usuario=self.usuario, titulo='Duna', externo_id='gb:abc', tipo='lido')
        buscar_mock.return_value = ResultadoBusca(
            livros=[LivroExterno(externo_id='gb:abc', titulo='Duna'), LivroExterno(externo_id='gb:xyz', titulo='Outro')],
            total=2, pagina=1, por_pagina=20, fonte='Google Books',
        )
        resposta = self.client.get(reverse('core:buscar'), {'q': 'duna'})
        self.assertEqual([status for _, status in resposta.context['itens']], ['lido', None])
        self.assertContains(resposta, 'Mover para')

    @mock.patch('core.views.buscar_livros')
    def test_buscar_mostra_erro_amigavel(self, buscar_mock):
        buscar_mock.return_value = ResultadoBusca(livros=[], total=0, pagina=1, por_pagina=20, erro='Fora do ar.')
        resposta = self.client.get(reverse('core:buscar'), {'q': 'duna'})
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Fora do ar.')

    def test_buscar_sem_termo_mostra_sugestoes(self):
        self.assertContains(self.client.get(reverse('core:buscar')), 'O que você quer ler hoje?')


# ==================== SERVIÇOS ====================

class NormalizacaoTests(TestCase):

    def test_utilidades(self):
        self.assertEqual(extrair_ano('2017-03-01'), '2017')
        self.assertEqual(extrair_ano(None), '')
        self.assertEqual(https('http://a.com/x'), 'https://a.com/x')

    def test_google_converte_resultado(self):
        with mock.patch('core.services.base.requests.get', return_value=resposta_json(GOOGLE_RESPOSTA)):
            resultado = GoogleBooks().buscar('duna', pagina=1, por_pagina=20)

        livro = resultado.livros[0]
        self.assertEqual(livro.externo_id, 'gb:abc123')
        self.assertEqual(livro.ano, '2017')
        self.assertEqual(livro.paginas, 680)
        self.assertEqual(livro.capa, 'https://books.google.com/capa.jpg')
        self.assertEqual(livro.descricao, 'Um clássico .')
        self.assertEqual(resultado.livros[1].autor, '')
        self.assertIsNone(resultado.livros[1].paginas)

    def test_google_envia_paginacao(self):
        with mock.patch('core.services.base.requests.get', return_value=resposta_json(GOOGLE_RESPOSTA)) as get:
            GoogleBooks().buscar('duna', pagina=3, por_pagina=20)
        self.assertEqual(get.call_args.kwargs['params']['startIndex'], 40)

    def test_openlibrary_converte_resultado(self):
        with mock.patch('core.services.base.requests.get', return_value=resposta_json(OPENLIBRARY_RESPOSTA)):
            livro = OpenLibrary().buscar('dom casmurro', pagina=1, por_pagina=20).livros[0]
        self.assertEqual(livro.externo_id, 'ol:OL1W')
        self.assertEqual(livro.capa, 'https://covers.openlibrary.org/b/id/42-M.jpg')
        self.assertEqual(livro.categoria, 'Romance brasileiro')
        self.assertEqual(livro.ano, '1899')


@override_settings(CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'testes'}})
class BuscarLivrosTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_usa_open_library_quando_google_falha(self):
        respostas = [resposta_json({}, status=429), resposta_json(OPENLIBRARY_RESPOSTA)]
        with mock.patch('core.services.base.requests.get', side_effect=respostas):
            resultado = buscar_livros('dom casmurro')
        self.assertEqual(resultado.fonte, 'Open Library')
        self.assertIn('Google Books', resultado.aviso)
        self.assertEqual(len(resultado.livros), 1)

    def test_resultado_de_fallback_fica_pouco_tempo_em_cache(self):
        respostas = [resposta_json({}, status=429), resposta_json(OPENLIBRARY_RESPOSTA)]
        with mock.patch('core.services.base.requests.get', side_effect=respostas), \
                mock.patch('core.services.cache.set') as cache_set:
            buscar_livros('dom casmurro')
        self.assertEqual(cache_set.call_args.args[2], 5 * 60)

    def test_erro_quando_todas_as_fontes_falham(self):
        with mock.patch('core.services.base.requests.get', side_effect=requests.ConnectionError('offline')):
            resultado = buscar_livros('qualquer')
        self.assertTrue(resultado.erro)
        self.assertEqual(resultado.livros, [])

    def test_resultado_fica_em_cache(self):
        with mock.patch('core.services.base.requests.get', return_value=resposta_json(GOOGLE_RESPOSTA)) as get:
            buscar_livros('duna')
            buscar_livros('  DUNA ')
        self.assertEqual(get.call_count, 1)

    def test_termo_vazio_nao_consulta_api(self):
        with mock.patch('core.services.base.requests.get') as get:
            self.assertEqual(buscar_livros('   ').livros, [])
        get.assert_not_called()
