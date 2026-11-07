from django.db.models import Count, Q
from django.utils.functional import SimpleLazyObject

from core.models import Livro


def _contar(usuario):
    return Livro.objects.do_usuario(usuario).aggregate(
        total=Count('id'),
        **{status: Count('id', filter=Q(tipo=status)) for status in Livro.Status.values},
    )


def contagem_estantes(request):
    """Disponibiliza a quantidade de livros por estante (usada no menu lateral)."""
    usuario = getattr(request, 'user', None)
    if usuario is None or not usuario.is_authenticated:
        return {}
    # Lazy: a consulta só roda se o template realmente usar o valor.
    return {'contagem_estantes': SimpleLazyObject(lambda: _contar(usuario))}
