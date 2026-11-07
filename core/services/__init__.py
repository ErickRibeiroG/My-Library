"""
Busca de livros em APIs externas.

Uso:
    resultado = buscar_livros('duna', pagina=1)
    resultado.livros  # lista de LivroExterno

O Google Books é a fonte principal; se ele falhar (timeout, limite de
requisições etc.), a Open Library é usada automaticamente. Resultados são
mantidos em cache para evitar chamadas repetidas.
"""

import hashlib
import logging

from django.conf import settings
from django.core.cache import cache

from .base import ErroBusca, LivroExterno, ResultadoBusca
from .googlebooks import GoogleBooks
from .openlibrary import OpenLibrary

logger = logging.getLogger(__name__)

POR_PAGINA = 20
FONTES = (GoogleBooks, OpenLibrary)
CACHE_FALLBACK_SEGUNDOS = 5 * 60

__all__ = ['ErroBusca', 'LivroExterno', 'ResultadoBusca', 'POR_PAGINA', 'buscar_livros']


def _chave_cache(query: str, pagina: int) -> str:
    digest = hashlib.sha256(query.strip().lower().encode()).hexdigest()[:32]
    return f'busca:v1:{digest}:{pagina}'


def buscar_livros(query: str, pagina: int = 1, por_pagina: int = POR_PAGINA) -> ResultadoBusca:
    query = (query or '').strip()
    pagina = max(1, int(pagina))

    if not query:
        return ResultadoBusca(livros=[], total=0, pagina=pagina, por_pagina=por_pagina)

    chave = _chave_cache(query, pagina)
    em_cache = cache.get(chave)
    if em_cache is not None:
        return em_cache

    erros = []
    for fonte_cls in FONTES:
        fonte = fonte_cls()
        try:
            resultado = fonte.buscar(query, pagina=pagina, por_pagina=por_pagina)
        except ErroBusca as exc:
            logger.warning('Falha na busca em %s: %s', fonte.nome, exc)
            erros.append(fonte.nome)
            continue

        tempo_cache = settings.BUSCA_CACHE_SEGUNDOS
        if erros:
            resultado.aviso = f'{", ".join(erros)} indisponível no momento — exibindo resultados de {fonte.nome}.'
            # Resultado de reserva: guarda por pouco tempo para voltar à fonte principal logo.
            tempo_cache = min(tempo_cache, CACHE_FALLBACK_SEGUNDOS)
        cache.set(chave, resultado, tempo_cache)
        return resultado

    return ResultadoBusca(
        livros=[],
        total=0,
        pagina=pagina,
        por_pagina=por_pagina,
        erro='Não foi possível consultar os serviços de busca agora. Tente novamente em instantes.',
    )
