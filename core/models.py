from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class LivroQuerySet(models.QuerySet):

    def do_usuario(self, usuario):
        return self.filter(usuario=usuario)

    def buscar(self, termo):
        if not termo:
            return self
        return self.filter(
            Q(titulo__icontains=termo) | Q(autor__icontains=termo) | Q(categoria__icontains=termo)
        )


class Livro(models.Model):

    class Status(models.TextChoices):
        QUERO = 'quero', 'Quero ler'
        COMPRADO = 'comprado', 'Comprado'
        LIDO = 'lido', 'Lido'

    AVALIACAO_CHOICES = [(n, f'{n} estrela{"s" if n > 1 else ""}') for n in range(1, 6)]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='livros',
    )
    externo_id = models.CharField(
        'ID externo',
        max_length=64,
        blank=True,
        help_text='Identificador na API de origem (ex.: gb:XXXX ou ol:OL123W).',
    )

    titulo = models.CharField('título', max_length=255)
    autor = models.CharField(max_length=255, blank=True)
    ano = models.CharField(max_length=10, blank=True)
    paginas = models.PositiveIntegerField('páginas', null=True, blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    capa = models.URLField(max_length=500, blank=True)
    descricao = models.TextField('descrição', blank=True)

    tipo = models.CharField('status', max_length=10, choices=Status.choices, default=Status.QUERO)
    avaliacao = models.PositiveSmallIntegerField(
        'avaliação',
        choices=AVALIACAO_CHOICES,
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    lido_em = models.DateField('lido em', null=True, blank=True)

    criado_em = models.DateTimeField('adicionado em', default=timezone.now, editable=False)
    atualizado_em = models.DateTimeField('atualizado em', auto_now=True)

    objects = LivroQuerySet.as_manager()

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'livro'
        verbose_name_plural = 'livros'
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'externo_id'],
                condition=~Q(externo_id=''),
                name='livro_externo_unico_por_usuario',
            ),
        ]
        indexes = [
            models.Index(fields=['usuario', 'tipo'], name='livro_usuario_tipo_idx'),
        ]

    def __str__(self):
        return self.titulo

    @property
    def link_externo(self):
        fonte, _, identificador = self.externo_id.partition(':')
        if not identificador:
            return ''
        if fonte == 'gb':
            return f'https://books.google.com/books?id={identificador}'
        if fonte == 'ol':
            return f'https://openlibrary.org/works/{identificador}'
        return ''

    def definir_status(self, novo_status):
        """Muda o status e mantém `lido_em` coerente."""
        self.tipo = novo_status
        if novo_status == self.Status.LIDO:
            self.lido_em = self.lido_em or timezone.localdate()
        else:
            self.lido_em = None
