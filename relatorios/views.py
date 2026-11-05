from django.db.models import Case, IntegerField, Value, When
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils.text import slugify
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import EhProfessor

from .models import Relatorio
from turmas.models import Turma

from .serializers import AvaliacaoSerializer, RelatorioDetalheSerializer, RelatorioResumoSerializer


def relatorios_do_professor(professor):
    return (
        Relatorio.objects.filter(turma__professor=professor)
        .exclude(status=Relatorio.Status.RASCUNHO)
        .select_related("aluno", "turma")
        .prefetch_related("fotos")
    )


class RelatoriosDaTurmaView(generics.ListAPIView):
    serializer_class = RelatorioResumoSerializer
    permission_classes = [IsAuthenticated, EhProfessor]
    pagination_class = None

    def get_queryset(self):
        turma = get_object_or_404(Turma, pk=self.kwargs["turma_id"], professor=self.request.user)
        return (
            relatorios_do_professor(self.request.user)
            .filter(turma=turma)
            .annotate(
                prioridade=Case(
                    When(status=Relatorio.Status.ENTREGUE, then=Value(0)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )
            .order_by("prioridade", "-entregue_em", "-id")
        )


class RelatorioDetalheView(generics.RetrieveAPIView):
    serializer_class = RelatorioDetalheSerializer
    permission_classes = [IsAuthenticated, EhProfessor]

    def get_queryset(self):
        return relatorios_do_professor(self.request.user)


class AvaliacaoView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def patch(self, request, pk):
        relatorio = get_object_or_404(relatorios_do_professor(request.user), pk=pk)
        serializer = AvaliacaoSerializer(relatorio, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(RelatorioDetalheSerializer(relatorio).data)


class RelatorioPdfView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def get(self, request, pk):
        relatorio = get_object_or_404(relatorios_do_professor(request.user), pk=pk)
        if not relatorio.pdf:
            raise Http404
        nome = f"relatorio-{slugify(relatorio.aluno.get_full_name() or relatorio.aluno_id)}.pdf"
        return FileResponse(relatorio.pdf.open("rb"), as_attachment=True, filename=nome, content_type="application/pdf")


class RelatorioFotoView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def get(self, request, pk, foto_id):
        relatorio = get_object_or_404(relatorios_do_professor(request.user), pk=pk)
        foto = get_object_or_404(relatorio.fotos, pk=foto_id)
        return FileResponse(foto.imagem.open("rb"))
