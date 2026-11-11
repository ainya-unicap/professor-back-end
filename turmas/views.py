from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.permissions import EhProfessor

from .consultas import turmas_do_professor
from .serializers import TurmaSerializer


class TurmaListaView(generics.ListCreateAPIView):
    serializer_class = TurmaSerializer
    permission_classes = [IsAuthenticated, EhProfessor]
    pagination_class = None

    def get_queryset(self):
        return turmas_do_professor(self.request.user)

    def perform_create(self, serializer):
        serializer.save(professor=self.request.user)


class TurmaDetalheView(generics.RetrieveAPIView):
    serializer_class = TurmaSerializer
    permission_classes = [IsAuthenticated, EhProfessor]

    def get_queryset(self):
        return turmas_do_professor(self.request.user)
