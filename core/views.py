from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.forms import FiltroBibliotecaForm, LivroForm
from core.models import Livro
from core.services import buscar_livros

LIVROS_POR_ESTANTE = 12
LIVROS_POR_PAGINA = 24

ESTANTES = [
    {
        'status': Livro.Status.QUERO,
        'titulo': 'Quero ler',
        'subtitulo': 'Sua lista de desejos',
        'icone': 'fa-brands fa-readme',
        'vazio': 'Busque livros e adicione à sua lista de leitura.',
    },
    {
        'status': Livro.Status.COMPRADO,
        'titulo': 'Comprados',
        'subtitulo': 'Livros que você já tem, esperando a vez',
        'icone': 'fa-solid fa-bag-shopping',
        'vazio': 'Marque livros como comprados para vê-los aqui.',
    },
    {
        'status': Livro.Status.LIDO,
        'titulo': 'Lidos',
        'subtitulo': 'Leituras concluídas',
        'icone': 'fa-solid fa-circle-check',
        'vazio': 'Quando terminar um livro, marque-o como lido.',
    },
]


def _voltar(request, padrao='core:home'):
    """Redireciona para o `next` enviado no formulário, se for seguro."""
    destino = request.POST.get('next') or request.GET.get('next')
    if destino and url_has_allowed_host_and_scheme(
        destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(destino)
    return redirect(padrao)


def _livro_do_usuario(request, pk):
    return get_object_or_404(Livro, pk=pk, usuario=request.user)


# ==================== PÁGINAS ====================

@login_required
def home(request):
    livros = Livro.objects.do_usuario(request.user)
    hoje = timezone.localdate()

    resumo = livros.aggregate(
        total=Count('id'),
        lidos=Count('id', filter=Q(tipo=Livro.Status.LIDO)),
        lidos_no_ano=Count('id', filter=Q(tipo=Livro.Status.LIDO, lido_em__year=hoje.year)),
        paginas_lidas=Sum('paginas', filter=Q(tipo=Livro.Status.LIDO)),
        media_avaliacao=Avg('avaliacao'),
    )
    resumo['percentual_lido'] = round(100 * resumo['lidos'] / resumo['total']) if resumo['total'] else 0

    estantes = []
    for estante in ESTANTES:
        da_estante = livros.filter(tipo=estante['status'])
        exibidos = list(da_estante[:LIVROS_POR_ESTANTE])
        total = da_estante.count() if len(exibidos) == LIVROS_POR_ESTANTE else len(exibidos)
        estantes.append({
            **estante,
            'livros': exibidos,
            'total': total,
            'restantes': total - len(exibidos),
        })

    return render(request, 'core/home.html', {
        'resumo': resumo,
        'estantes': estantes,
        'ano_atual': hoje.year,
    })


@login_required
def biblioteca(request):
    filtro = FiltroBibliotecaForm(request.GET or None)
    livros = filtro.aplicar(Livro.objects.do_usuario(request.user))

    pagina = Paginator(livros, LIVROS_POR_PAGINA).get_page(request.GET.get('pagina'))

    status_atual = request.GET.get('status', '')
    status_atual = status_atual if status_atual in Livro.Status.values else ''
    return render(request, 'core/livros.html', {
        'status_atual': status_atual,
        'mostrar_status': not status_atual,
        'busca_atual': request.GET.get('q', ''),
        'ordem_atual': request.GET.get('ordem', 'recentes'),
        'ordens': [(chave, rotulo) for chave, (rotulo, _) in FiltroBibliotecaForm.ORDENS.items()],
        'page_obj': pagina,
        'faixa_paginas': pagina.paginator.get_elided_page_range(pagina.number, on_each_side=2, on_ends=1),
    })


@login_required
def buscar(request):
    query = request.GET.get('q', '').strip()[:200]
    try:
        numero_pagina = max(1, int(request.GET.get('pagina', 1)))
    except ValueError:
        numero_pagina = 1

    resultado = buscar_livros(query, pagina=numero_pagina) if query else None

    itens = []
    faixa_paginas = []
    if resultado:
        ids = [livro.externo_id for livro in resultado.livros if livro.externo_id]
        na_biblioteca = dict(
            Livro.objects.do_usuario(request.user)
            .filter(externo_id__in=ids)
            .values_list('externo_id', 'tipo')
        )
        itens = [(livro, na_biblioteca.get(livro.externo_id)) for livro in resultado.livros]
        if resultado.total_paginas > 1:
            faixa_paginas = Paginator(range(resultado.total_paginas), 1).get_elided_page_range(
                min(numero_pagina, resultado.total_paginas), on_each_side=2, on_ends=1
            )

    return render(request, 'core/buscar.html', {
        'query': query,
        'resultado': resultado,
        'itens': itens,
        'faixa_paginas': faixa_paginas,
        'sugestoes': ['Machado de Assis', 'Clarice Lispector', 'Ficção científica', 'Tolkien', 'Hábitos', 'Filosofia'],
    })


@login_required
def detalhe(request, pk):
    livro = _livro_do_usuario(request, pk)
    return render(request, 'core/detalhe.html', {'livro': livro})


# ==================== AÇÕES (POST) ====================

@login_required
@require_POST
def adicionar(request):
    form = LivroForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Não foi possível adicionar este livro: dados inválidos.')
        return _voltar(request, 'core:buscar')

    dados = form.cleaned_data
    status = dados['tipo']
    rotulo = Livro.Status(status).label

    existente = None
    if dados['externo_id']:
        existente = Livro.objects.do_usuario(request.user).filter(externo_id=dados['externo_id']).first()

    if existente:
        if existente.tipo == status:
            messages.info(request, f'“{existente.titulo}” já está em “{rotulo}”.')
        else:
            existente.definir_status(status)
            existente.save()
            messages.success(request, f'“{existente.titulo}” foi movido para “{rotulo}”.')
        return _voltar(request, 'core:buscar')

    livro = form.save(commit=False)
    livro.usuario = request.user
    livro.definir_status(status)
    livro.save()
    messages.success(request, f'“{livro.titulo}” foi adicionado a “{rotulo}”.')
    return _voltar(request, 'core:buscar')


@login_required
@require_POST
def alterar_status(request, pk):
    livro = _livro_do_usuario(request, pk)
    novo_status = request.POST.get('tipo')

    if novo_status not in Livro.Status.values:
        messages.error(request, 'Status inválido.')
        return _voltar(request)

    if novo_status != livro.tipo:
        livro.definir_status(novo_status)
        livro.save()
        messages.success(request, f'“{livro.titulo}” foi movido para “{Livro.Status(novo_status).label}”.')
    return _voltar(request)


@login_required
@require_POST
def avaliar(request, pk):
    livro = _livro_do_usuario(request, pk)

    try:
        nota = int(request.POST.get('avaliacao', ''))
    except ValueError:
        nota = -1

    if nota == 0:
        livro.avaliacao = None
        livro.save(update_fields=['avaliacao', 'atualizado_em'])
        messages.info(request, f'Avaliação de “{livro.titulo}” removida.')
    elif 1 <= nota <= 5:
        livro.avaliacao = nota
        livro.save(update_fields=['avaliacao', 'atualizado_em'])
        messages.success(request, f'Você deu {nota} estrela{"s" if nota > 1 else ""} para “{livro.titulo}”.')
    else:
        messages.error(request, 'A avaliação deve ser de 1 a 5 estrelas.')
    return _voltar(request)


@login_required
@require_POST
def remover(request, pk):
    livro = _livro_do_usuario(request, pk)
    titulo = livro.titulo
    livro.delete()
    messages.success(request, f'“{titulo}” foi removido da sua biblioteca.')
    return _voltar(request)
