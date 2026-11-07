import zlib

from django import template

from core.models import Livro

register = template.Library()

STATUS_ICONES = {
    Livro.Status.QUERO: 'fa-brands fa-readme',
    Livro.Status.COMPRADO: 'fa-solid fa-bag-shopping',
    Livro.Status.LIDO: 'fa-solid fa-circle-check',
}


@register.filter
def matiz(texto):
    """Matiz (0–359) estável derivado de um texto — usado nas capas sem imagem."""
    return zlib.crc32(str(texto or '').encode()) % 360


@register.filter
def iniciais(usuario):
    nome = f'{usuario.first_name} {usuario.last_name}'.split()
    if nome:
        return ''.join(parte[0] for parte in (nome[0], nome[-1]) if parte).upper()[:2]
    return (usuario.get_username() or '?')[:1].upper()


@register.filter
def rotulo_status(status):
    try:
        return Livro.Status(status).label
    except ValueError:
        return ''


@register.filter
def icone_status(status):
    return STATUS_ICONES.get(status, 'fa-solid fa-book')


@register.filter
def get_item(dicionario, chave):
    try:
        return dicionario[chave]
    except (KeyError, TypeError):
        return ''


@register.simple_tag
def status_disponiveis():
    return [(valor, rotulo, STATUS_ICONES[valor]) for valor, rotulo in Livro.Status.choices]
