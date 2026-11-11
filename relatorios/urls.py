from django.urls import path

from .views import RelatorioPdfView, RelatoriosDaTurmaView

urlpatterns = [
    path("turmas/<int:turma_id>/relatorios/", RelatoriosDaTurmaView.as_view(), name="relatorios_da_turma"),
    path("relatorios/<int:pk>/pdf/", RelatorioPdfView.as_view(), name="relatorio_pdf"),
]
