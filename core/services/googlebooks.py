from django.conf import settings

from .base import (
    FonteDeLivros,
    LivroExterno,
    ResultadoBusca,
    cortar,
    extrair_ano,
    https,
    inteiro_positivo,
    texto_limpo,
)


class GoogleBooks(FonteDeLivros):
    nome = 'Google Books'
    URL = 'https://www.googleapis.com/books/v1/volumes'

    def buscar(self, query: str, pagina: int, por_pagina: int) -> ResultadoBusca:
        params = {
            'q': query,
            'startIndex': (pagina - 1) * por_pagina,
            'maxResults': min(por_pagina, 40),
            'printType': 'books',
        }
        if settings.GOOGLE_BOOKS_API_KEY:
            params['key'] = settings.GOOGLE_BOOKS_API_KEY

        dados = self._get_json(self.URL, params)

        livros = [self._converter(item) for item in dados.get('items', [])]
        return ResultadoBusca(
            livros=[livro for livro in livros if livro.titulo],
            total=int(dados.get('totalItems') or 0),
            pagina=pagina,
            por_pagina=por_pagina,
            fonte=self.nome,
        )

    @staticmethod
    def _converter(item: dict) -> LivroExterno:
        info = item.get('volumeInfo', {})
        imagens = info.get('imageLinks', {})
        capa = imagens.get('thumbnail') or imagens.get('smallThumbnail') or ''

        titulo = info.get('title') or ''
        if info.get('subtitle'):
            titulo = f'{titulo}: {info["subtitle"]}'

        return LivroExterno(
            externo_id=f'gb:{item.get("id", "")}'[:64],
            titulo=cortar(titulo, 255),
            autor=cortar(', '.join(info.get('authors', [])), 255),
            ano=extrair_ano(info.get('publishedDate')),
            paginas=inteiro_positivo(info.get('pageCount')),
            categoria=cortar((info.get('categories') or [''])[0], 100),
            capa=cortar(https(capa).replace('&edge=curl', ''), 500),
            descricao=cortar(texto_limpo(info.get('description')), 2000),
        )


def procurar_livros_g(query):
    """Compatibilidade com a função antiga: retorna apenas a 1ª página."""
    return GoogleBooks().buscar(query, pagina=1, por_pagina=20).livros
