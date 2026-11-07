import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Etapa 3/3: dono obrigatório, ordenação, índice e unicidade por usuário."""

    dependencies = [
        ('core', '0006_atribuir_livros_existentes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='livro',
            name='usuario',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='livros',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name='livro',
            options={'ordering': ['-criado_em'], 'verbose_name': 'livro', 'verbose_name_plural': 'livros'},
        ),
        migrations.AddIndex(
            model_name='livro',
            index=models.Index(fields=['usuario', 'tipo'], name='livro_usuario_tipo_idx'),
        ),
        migrations.AddConstraint(
            model_name='livro',
            constraint=models.UniqueConstraint(
                condition=models.Q(('externo_id', ''), _negated=True),
                fields=('usuario', 'externo_id'),
                name='livro_externo_unico_por_usuario',
            ),
        ),
    ]
