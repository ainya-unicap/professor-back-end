from django.urls import path

from .views import (
    PainelView,
    PendentesView,
    TurmaDetalheView,
    TurmaListaView,
    TurmaNovoCodigoView,
    TurmaPrazosView,
)

urlpatterns = [
    path("turmas/", TurmaListaView.as_view(), name="turmas"),
    path("turmas/<int:pk>/", TurmaDetalheView.as_view(), name="turma"),
    path("turmas/<int:pk>/prazos/", TurmaPrazosView.as_view(), name="turma_prazos"),
    path("turmas/<int:pk>/novo-codigo/", TurmaNovoCodigoView.as_view(), name="turma_novo_codigo"),
    path("professor/painel/", PainelView.as_view(), name="painel"),
    path("professor/pendentes/", PendentesView.as_view(), name="pendentes"),
]
