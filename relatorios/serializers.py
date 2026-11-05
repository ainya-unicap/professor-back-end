from django.utils import timezone
from rest_framework import serializers

from .models import Relatorio


class RelatorioDetalheSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    turma = serializers.SerializerMethodField()
    fotos = serializers.SerializerMethodField()
    tem_pdf = serializers.SerializerMethodField()
    anterior = serializers.SerializerMethodField()
    proximo = serializers.SerializerMethodField()

    class Meta:
        model = Relatorio
        fields = [
            "id",
            "aluno",
            "turma",
            "planta",
            "status",
            "entregue_em",
            "introducao",
            "objetivo",
            "desenvolvimento",
            "conclusao",
            "referencias",
            "fotos",
            "tem_pdf",
            "nota",
            "feedback",
            "corrigido_em",
            "anterior",
            "proximo",
        ]

    def get_aluno(self, relatorio):
        return {"id": relatorio.aluno_id, "nome": relatorio.aluno.get_full_name() or relatorio.aluno.email}

    def get_turma(self, relatorio):
        turma = relatorio.turma
        return {
            "id": turma.id,
            "nome": turma.nome,
            "periodo": turma.periodo,
            "prazo_correcao": turma.prazo_correcao,
        }

    def get_fotos(self, relatorio):
        return [{"id": foto.id, "legenda": foto.legenda} for foto in relatorio.fotos.all()]

    def get_tem_pdf(self, relatorio):
        return bool(relatorio.pdf)

    def _vizinhos(self, relatorio):
        if not hasattr(self, "_cache_vizinhos"):
            ids = list(
                Relatorio.objects.filter(turma=relatorio.turma)
                .exclude(status=Relatorio.Status.RASCUNHO)
                .order_by("entregue_em", "id")
                .values_list("id", flat=True)
            )
            posicao = ids.index(relatorio.id) if relatorio.id in ids else None
            if posicao is None:
                self._cache_vizinhos = (None, None)
            else:
                self._cache_vizinhos = (
                    ids[posicao - 1] if posicao > 0 else None,
                    ids[posicao + 1] if posicao < len(ids) - 1 else None,
                )
        return self._cache_vizinhos

    def get_anterior(self, relatorio):
        return self._vizinhos(relatorio)[0]

    def get_proximo(self, relatorio):
        return self._vizinhos(relatorio)[1]


class AvaliacaoSerializer(serializers.ModelSerializer):
    concluir = serializers.BooleanField(write_only=True, default=False)

    class Meta:
        model = Relatorio
        fields = ["nota", "feedback", "concluir"]
        extra_kwargs = {
            "nota": {
                "error_messages": {
                    "max_value": "A nota vai de 0 a 10.",
                    "min_value": "A nota vai de 0 a 10.",
                    "invalid": "Informe um número, por exemplo 8,5.",
                    "max_decimal_places": "Use no máximo duas casas decimais.",
                }
            }
        }

    def validate(self, attrs):
        nota = attrs.get("nota", self.instance.nota if self.instance else None)
        if attrs.get("concluir") and nota is None:
            raise serializers.ValidationError({"nota": "Informe a nota para marcar como corrigido."})
        return attrs

    def update(self, relatorio, validated_data):
        concluir = validated_data.pop("concluir", False)
        for campo, valor in validated_data.items():
            setattr(relatorio, campo, valor)
        if concluir:
            relatorio.status = Relatorio.Status.CORRIGIDO
            relatorio.corrigido_em = timezone.now()
        relatorio.save()
        return relatorio


class RelatorioResumoSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    tem_pdf = serializers.SerializerMethodField()

    class Meta:
        model = Relatorio
        fields = ["id", "aluno", "planta", "status", "entregue_em", "tem_pdf"]

    def get_aluno(self, relatorio):
        return relatorio.aluno.get_full_name() or relatorio.aluno.email

    def get_tem_pdf(self, relatorio):
        return bool(relatorio.pdf)
