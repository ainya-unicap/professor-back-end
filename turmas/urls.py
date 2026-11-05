from django.urls import path

from .views import PainelView, TurmaListaView

urlpatterns = [
    path("turmas/", TurmaListaView.as_view(), name="turmas"),
    path("professor/painel/", PainelView.as_view(), name="painel"),
]
