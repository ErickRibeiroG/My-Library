import re

from django.db import migrations


def normalizar(apps, schema_editor):
    """
    Ajusta livros salvos antes desta versão:
    - capas em http:// passam para https:// (evita bloqueio de conteúdo misto);
    - remove o efeito de "página dobrada" (&edge=curl) das capas do Google Books;
    - o campo ano guarda só o ano (antes podia vir "2018-08-31").
    """
    Livro = apps.get_model('core', 'Livro')
    for livro in Livro.objects.all().only('id', 'capa', 'ano'):
        capa = livro.capa
        if capa.startswith('http://'):
            capa = 'https://' + capa[len('http://'):]
        capa = capa.replace('&edge=curl', '')

        encontrado = re.search(r'\d{4}', livro.ano or '')
        ano = encontrado.group(0) if encontrado else ''

        if capa != livro.capa or ano != livro.ano:
            Livro.objects.filter(pk=livro.pk).update(capa=capa, ano=ano)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_livro_usuario_obrigatorio'),
    ]

    operations = [
        migrations.RunPython(normalizar, migrations.RunPython.noop),
    ]
