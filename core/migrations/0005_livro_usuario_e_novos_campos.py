import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Etapa 1/3: adiciona os novos campos (dono ainda opcional)."""

    dependencies = [
        ('core', '0004_livro_avaliacao'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='livro',
            name='usuario',
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='livros',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='livro',
            name='externo_id',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Identificador na API de origem (ex.: gb:XXXX ou ol:OL123W).',
                max_length=64,
                verbose_name='ID externo',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='livro',
            name='descricao',
            field=models.TextField(blank=True, default='', verbose_name='descrição'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='livro',
            name='lido_em',
            field=models.DateField(blank=True, null=True, verbose_name='lido em'),
        ),
        migrations.AddField(
            model_name='livro',
            name='criado_em',
            field=models.DateTimeField(
                default=django.utils.timezone.now, editable=False, verbose_name='adicionado em'
            ),
        ),
        migrations.AddField(
            model_name='livro',
            name='atualizado_em',
            field=models.DateTimeField(auto_now=True, verbose_name='atualizado em'),
        ),
        migrations.AlterField(
            model_name='livro',
            name='titulo',
            field=models.CharField(max_length=255, verbose_name='título'),
        ),
        migrations.AlterField(
            model_name='livro',
            name='autor',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='livro',
            name='capa',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AlterField(
            model_name='livro',
            name='paginas',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='páginas'),
        ),
        migrations.AlterField(
            model_name='livro',
            name='tipo',
            field=models.CharField(
                choices=[('quero', 'Quero ler'), ('comprado', 'Comprado'), ('lido', 'Lido')],
                default='quero',
                max_length=10,
                verbose_name='status',
            ),
        ),
        migrations.AlterField(
            model_name='livro',
            name='avaliacao',
            field=models.PositiveSmallIntegerField(
                blank=True,
                choices=[
                    (1, '1 estrela'),
                    (2, '2 estrelas'),
                    (3, '3 estrelas'),
                    (4, '4 estrelas'),
                    (5, '5 estrelas'),
                ],
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
                verbose_name='avaliação',
            ),
        ),
    ]
