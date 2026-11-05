from django.contrib import admin

from .models import Matricula, Turma


class MatriculaInline(admin.TabularInline):
    model = Matricula
    extra = 0
    autocomplete_fields = ["aluno"]


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ["nome", "periodo", "instituicao", "professor", "codigo_convite", "ativa"]
    list_filter = ["periodo", "ativa"]
    search_fields = ["nome", "codigo_convite", "professor__email"]
    readonly_fields = ["codigo_convite", "criada_em"]
    inlines = [MatriculaInline]
