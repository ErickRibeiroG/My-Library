import re
from dataclasses import dataclass

import requests
from django.conf import settings


class ErroBusca(Exception):
    """Falha ao consultar uma API externa."""


@dataclass
class LivroExterno:
    externo_id: str
    titulo: str
    autor: str = ''
    ano: str = ''
    paginas: int | None = None
    categoria: str = ''
    capa: str = ''
    descricao: str = ''

    def como_dados_formulario(self) -> dict:
        return {
            'externo_id': self.externo_id,
            'titulo': self.titulo,
            'autor': self.autor,
            'ano': self.ano,
            'paginas': self.paginas or '',
            'categoria': self.categoria,
            'capa': self.capa,
            'descricao': self.descricao,
        }


@dataclass
class ResultadoBusca:
    livros: list[LivroExterno]
    total: int
    pagina: int
    por_pagina: int
    fonte: str = ''
    aviso: str = ''
    erro: str = ''

    @property
    def total_paginas(self) -> int:
        if not self.total:
            return 1 if self.livros else 0
        # As APIs costumam falhar em páginas muito distantes; limitamos a navegação.
        return min(-(-self.total // self.por_pagina), 25)

    @property
    def tem_anterior(self) -> bool:
        return self.pagina > 1

    @property
    def tem_proxima(self) -> bool:
        return self.pagina < self.total_paginas and len(self.livros) >= self.por_pagina


class FonteDeLivros:
    nome = ''

    def _get_json(self, url: str, params: dict) -> dict:
        try:
            resposta = requests.get(
                url,
                params=params,
                timeout=settings.BUSCA_TIMEOUT_SEGUNDOS,
                headers={'User-Agent': 'MyLibrary/1.0 (projeto pessoal)'},
            )
            resposta.raise_for_status()
            return resposta.json()
        except requests.RequestException as exc:
            raise ErroBusca(str(exc)) from exc
        except ValueError as exc:  # JSON inválido
            raise ErroBusca('Resposta inválida da API') from exc

    def buscar(self, query: str, pagina: int, por_pagina: int) -> ResultadoBusca:
        raise NotImplementedError


# ==================== utilidades de normalização ====================

_TAGS_HTML = re.compile(r'<[^>]+>')


def cortar(texto, limite: int) -> str:
    texto = (texto or '').strip()
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + '…'


def extrair_ano(data) -> str:
    correspondencia = re.search(r'\d{4}', str(data or ''))
    return correspondencia.group(0) if correspondencia else ''


def inteiro_positivo(valor) -> int | None:
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        return None
    return numero if numero > 0 else None


def https(url) -> str:
    url = (url or '').strip()
    if url.startswith('http://'):
        url = 'https://' + url[len('http://'):]
    return url


def texto_limpo(html) -> str:
    return re.sub(r'\s+', ' ', _TAGS_HTML.sub(' ', html or '')).strip()
