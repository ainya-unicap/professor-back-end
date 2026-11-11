from django.contrib import admin

from .models import Relatorio


@admin.register(Relatorio)
class RelatorioAdmin(admin.ModelAdmin):
    list_display = ["aluno", "turma", "planta", "status", "entregue_em"]
    list_filter = ["status", "turma__periodo"]
    search_fields = ["aluno__email", "aluno__first_name", "planta", "turma__nome"]
    autocomplete_fields = ["aluno"]
