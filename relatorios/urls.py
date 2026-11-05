from django.urls import path

from .views import (
    AvaliacaoView,
    RelatorioDetalheView,
    RelatorioFotoView,
    RelatorioPdfView,
    RelatoriosDaTurmaView,
)

urlpatterns = [
    path("turmas/<int:turma_id>/relatorios/", RelatoriosDaTurmaView.as_view(), name="relatorios_da_turma"),
    path("relatorios/<int:pk>/", RelatorioDetalheView.as_view(), name="relatorio"),
    path("relatorios/<int:pk>/avaliacao/", AvaliacaoView.as_view(), name="relatorio_avaliacao"),
    path("relatorios/<int:pk>/pdf/", RelatorioPdfView.as_view(), name="relatorio_pdf"),
    path("relatorios/<int:pk>/fotos/<int:foto_id>/", RelatorioFotoView.as_view(), name="relatorio_foto"),
]
