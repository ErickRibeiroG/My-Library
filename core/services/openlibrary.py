from .base import FonteDeLivros, LivroExterno, ResultadoBusca, cortar, inteiro_positivo

# Assuntos genéricos demais para servir de "categoria".
_ASSUNTOS_IGNORADOS = {'accessible book', 'protected daisy', 'in library', 'lending library'}


class OpenLibrary(FonteDeLivros):
    nome = 'Open Library'
    URL = 'https://openlibrary.org/search.json'
    CAMPOS = 'key,title,subtitle,author_name,first_publish_year,cover_i,number_of_pages_median,subject'

    def buscar(self, query: str, pagina: int, por_pagina: int) -> ResultadoBusca:
        dados = self._get_json(
            self.URL,
            {'q': query, 'page': pagina, 'limit': por_pagina, 'fields': self.CAMPOS},
        )
        livros = [self._converter(doc) for doc in dados.get('docs', [])]
        return ResultadoBusca(
            livros=[livro for livro in livros if livro.titulo],
            total=int(dados.get('numFound') or 0),
            pagina=pagina,
            por_pagina=por_pagina,
            fonte=self.nome,
        )

    @staticmethod
    def _converter(doc: dict) -> LivroExterno:
        capa_id = doc.get('cover_i')
        capa = f'https://covers.openlibrary.org/b/id/{capa_id}-M.jpg' if capa_id else ''

        categoria = next(
            (s for s in doc.get('subject', []) if s.lower() not in _ASSUNTOS_IGNORADOS),
            '',
        )
        chave = (doc.get('key') or '').rsplit('/', 1)[-1]

        titulo = doc.get('title') or ''
        if doc.get('subtitle'):
            titulo = f'{titulo}: {doc["subtitle"]}'

        return LivroExterno(
            externo_id=f'ol:{chave}'[:64] if chave else '',
            titulo=cortar(titulo, 255),
            autor=cortar(', '.join(doc.get('author_name', [])), 255),
            ano=str(doc.get('first_publish_year') or ''),
            paginas=inteiro_positivo(doc.get('number_of_pages_median')),
            categoria=cortar(categoria, 100),
            capa=capa,
        )


def procurar_livros(query):
    """Compatibilidade com a função antiga: retorna apenas a 1ª página."""
    return OpenLibrary().buscar(query, pagina=1, por_pagina=20).livros
