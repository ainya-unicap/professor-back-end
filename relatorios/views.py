from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.permissions import EhProfessor
from turmas.models import Turma

from .models import Relatorio
from .serializers import RelatorioResumoSerializer


def relatorios_entregues_do_professor(professor):
    return Relatorio.objects.filter(
        turma__professor=professor,
        status=Relatorio.Status.ENTREGUE,
    ).select_related("aluno", "turma")


class RelatoriosDaTurmaView(generics.ListAPIView):
    serializer_class = RelatorioResumoSerializer
    permission_classes = [IsAuthenticated, EhProfessor]
    pagination_class = None

    def get_queryset(self):
        turma = get_object_or_404(Turma, pk=self.kwargs["turma_id"], professor=self.request.user)
        return relatorios_entregues_do_professor(self.request.user).filter(turma=turma).order_by("-entregue_em", "-id")


class RelatorioPdfView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def get(self, request, pk):
        relatorio = get_object_or_404(relatorios_entregues_do_professor(request.user), pk=pk)
        if not relatorio.pdf:
            raise Http404
        nome = f"relatorio-{slugify(relatorio.aluno.get_full_name() or relatorio.aluno_id)}.pdf"
        return FileResponse(relatorio.pdf.open("rb"), as_attachment=True, filename=nome, content_type="application/pdf")
