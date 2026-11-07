from django.contrib import admin

from core.models import Livro


@admin.register(Livro)
class LivroAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'autor', 'usuario', 'tipo', 'avaliacao', 'paginas', 'criado_em')
    list_filter = ('tipo', 'avaliacao', 'categoria')
    search_fields = ('titulo', 'autor', 'categoria', 'usuario__email', 'usuario__username')
    list_select_related = ('usuario',)
    autocomplete_fields = ('usuario',)
    readonly_fields = ('criado_em', 'atualizado_em')
    date_hierarchy = 'criado_em'
    fieldsets = (
        (None, {'fields': ('usuario', 'titulo', 'autor', 'categoria')}),
        ('Detalhes', {'fields': ('ano', 'paginas', 'capa', 'descricao', 'externo_id')}),
        ('Leitura', {'fields': ('tipo', 'avaliacao', 'lido_em')}),
        ('Registro', {'fields': ('criado_em', 'atualizado_em')}),
    )
