from rest_framework import serializers

from relatorios.models import Relatorio

from .models import Turma


class TurmaSerializer(serializers.ModelSerializer):
    alunos = serializers.SerializerMethodField()
    relatorios_entregues = serializers.SerializerMethodField()

    class Meta:
        model = Turma
        fields = [
            "id",
            "nome",
            "periodo",
            "instituicao",
            "codigo_convite",
            "ativa",
            "alunos",
            "relatorios_entregues",
            "inicio_registros",
            "encerramento_registros",
            "limite_entrega",
            "prazo_correcao",
            "aceitar_atrasadas",
        ]
        read_only_fields = [
            "codigo_convite",
            "ativa",
            "inicio_registros",
            "encerramento_registros",
            "limite_entrega",
            "prazo_correcao",
            "aceitar_atrasadas",
        ]
        validators = []

    def get_alunos(self, turma):
        return getattr(turma, "total_alunos", 0)

    def get_relatorios_entregues(self, turma):
        return getattr(turma, "total_entregues", 0)

    def validate_nome(self, valor):
        return " ".join(valor.split())

    def validate_instituicao(self, valor):
        return " ".join(valor.split())

    def validate(self, attrs):
        professor = self.context["request"].user
        nome = attrs.get("nome", getattr(self.instance, "nome", None))
        periodo = attrs.get("periodo", getattr(self.instance, "periodo", None))
        repetidas = Turma.objects.filter(professor=professor, nome__iexact=nome, periodo=periodo)
        if self.instance:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(
                {"nome": "Você já tem uma turma com esse nome neste período."}
            )
        return attrs


class RelatorioPendenteSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    turma = serializers.CharField(source="turma.nome")

    class Meta:
        model = Relatorio
        fields = ["id", "aluno", "planta", "turma", "entregue_em"]

    def get_aluno(self, relatorio):
        return relatorio.aluno.get_full_name() or relatorio.aluno.email
