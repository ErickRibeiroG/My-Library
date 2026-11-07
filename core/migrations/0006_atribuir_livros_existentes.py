from django.conf import settings
from django.db import migrations


def atribuir_dono(apps, schema_editor):
    """
    Etapa 2/3: antes desta versão os livros não tinham dono. Eles passam a
    pertencer ao usuário que fez login mais recentemente (ou ao primeiro
    cadastrado). Sem nenhum usuário, livros órfãos ficariam inacessíveis e
    são removidos.
    """
    Livro = apps.get_model('core', 'Livro')
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    User = apps.get_model(app_label, model_name)

    orfaos = Livro.objects.filter(usuario__isnull=True)
    if not orfaos.exists():
        return

    dono = (
        User.objects.filter(last_login__isnull=False).order_by('-last_login').first()
        or User.objects.order_by('id').first()
    )
    if dono is None:
        orfaos.delete()
        return
    orfaos.update(usuario=dono)


def normalizar_dados(apps, schema_editor):
    Livro = apps.get_model('core', 'Livro')
    # Antes, "0 páginas" significava "desconhecido".
    Livro.objects.filter(paginas=0).update(paginas=None)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_livro_usuario_e_novos_campos'),
    ]

    operations = [
        migrations.RunPython(atribuir_dono, migrations.RunPython.noop),
        migrations.RunPython(normalizar_dados, migrations.RunPython.noop),
    ]
