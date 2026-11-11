from django.urls import path

from .views import TurmaDetalheView, TurmaListaView

urlpatterns = [
    path("turmas/", TurmaListaView.as_view(), name="turmas"),
    path("turmas/<int:pk>/", TurmaDetalheView.as_view(), name="turma"),
]
