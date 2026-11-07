from django import forms
from django.db.models import F

from core.models import Livro


class LivroForm(forms.ModelForm):
    """Valida os dados de um livro vindo da busca antes de salvá-lo."""

    class Meta:
        model = Livro
        fields = ['externo_id', 'titulo', 'autor', 'ano', 'paginas', 'categoria', 'capa', 'descricao', 'tipo']


class FiltroBibliotecaForm(forms.Form):
    ORDENS = {
        'recentes': ('Adicionados recentemente', ['-criado_em']),
        'titulo': ('Título (A–Z)', ['titulo']),
        'autor': ('Autor (A–Z)', ['autor', 'titulo']),
        'avaliacao': ('Melhor avaliados', [F('avaliacao').desc(nulls_last=True), 'titulo']),
        'ano': ('Ano de publicação', ['-ano', 'titulo']),
    }

    q = forms.CharField(required=False, max_length=100)
    status = forms.ChoiceField(required=False, choices=[('', 'Todos'), *Livro.Status.choices])
    ordem = forms.ChoiceField(
        required=False,
        choices=[(chave, rotulo) for chave, (rotulo, _) in ORDENS.items()],
    )

    def aplicar(self, queryset):
        if not self.is_valid():
            return queryset
        dados = self.cleaned_data
        queryset = queryset.buscar(dados.get('q'))
        if dados.get('status'):
            queryset = queryset.filter(tipo=dados['status'])
        _, ordenacao = self.ORDENS.get(dados.get('ordem') or 'recentes')
        return queryset.order_by(*ordenacao)
