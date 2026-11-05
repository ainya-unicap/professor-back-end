from django.db.models import Max, Min
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import EhProfessor
from relatorios.models import Relatorio

from .consultas import turmas_do_professor
from .models import Matricula
from .serializers import (
    PrazosSerializer,
    RelatorioPendenteSerializer,
    TurmaDetalheSerializer,
    TurmaSerializer,
)

LIMITE_TURMAS_PAINEL = 3
LIMITE_PENDENTES_PAINEL = 4


class TurmaListaView(generics.ListCreateAPIView):
    serializer_class = TurmaSerializer
    permission_classes = [IsAuthenticated, EhProfessor]
    pagination_class = None

    def get_queryset(self):
        return turmas_do_professor(self.request.user)

    def perform_create(self, serializer):
        serializer.save(professor=self.request.user)


class TurmaDetalheView(generics.RetrieveAPIView):
    serializer_class = TurmaDetalheSerializer
    permission_classes = [IsAuthenticated, EhProfessor]

    def get_queryset(self):
        return turmas_do_professor(self.request.user).prefetch_related("relatorios")


class TurmaPrazosView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def patch(self, request, pk):
        turma = get_object_or_404(turmas_do_professor(request.user), pk=pk)
        serializer = PrazosSerializer(turma, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PrazosSerializer(turma).data)


class TurmaNovoCodigoView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def post(self, request, pk):
        turma = get_object_or_404(turmas_do_professor(request.user), pk=pk)
        turma.gerar_novo_codigo()
        return Response({"codigo_convite": turma.codigo_convite, "link_convite": turma.link_convite})


class PendentesView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def get(self, request):
        total = Relatorio.objects.filter(
            turma__professor=request.user,
            turma__ativa=True,
            status=Relatorio.Status.ENTREGUE,
        ).count()
        return Response({"aguardando_correcao": total})


class PainelView(APIView):
    permission_classes = [IsAuthenticated, EhProfessor]

    def get(self, request):
        turmas = turmas_do_professor(request.user).filter(ativa=True)
        pendentes = (
            Relatorio.objects.filter(
                turma__in=turmas,
                status=Relatorio.Status.ENTREGUE,
            )
            .select_related("aluno", "turma")
            .order_by("entregue_em")
        )
        hoje = timezone.localdate()
        agregados = turmas.aggregate(periodo_atual=Max("periodo"))
        prazo = turmas.filter(prazo_correcao__gte=hoje).aggregate(proximo=Min("prazo_correcao"))
        recente = turmas.order_by("-periodo", "-criada_em").first()

        return Response(
            {
                "periodo_atual": agregados["periodo_atual"],
                "instituicao": recente.instituicao if recente else None,
                "resumo": {
                    "aguardando_correcao": pendentes.count(),
                    "turmas_com_pendencia": pendentes.values("turma").distinct().count(),
                    "turmas_ativas": turmas.count(),
                    "alunos": Matricula.objects.filter(turma__in=turmas)
                    .values("aluno")
                    .distinct()
                    .count(),
                    "prazo_avaliacao": prazo["proximo"],
                },
                "turmas": TurmaSerializer(
                    turmas.order_by("-periodo", "nome")[:LIMITE_TURMAS_PAINEL],
                    many=True,
                ).data,
                "aguardando": RelatorioPendenteSerializer(
                    pendentes[:LIMITE_PENDENTES_PAINEL],
                    many=True,
                ).data,
            }
        )
