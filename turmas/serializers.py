from rest_framework import serializers

from .models import Turma


class TurmaSerializer(serializers.ModelSerializer):
    link_convite = serializers.CharField(read_only=True)
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
            "link_convite",
            "ativa",
            "alunos",
            "relatorios_entregues",
        ]
        read_only_fields = ["codigo_convite", "ativa"]
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
        repetidas = Turma.objects.filter(
            professor=professor,
            nome__iexact=attrs.get("nome"),
            periodo=attrs.get("periodo"),
        )
        if repetidas.exists():
            raise serializers.ValidationError(
                {"nome": "Você já tem uma turma com esse nome neste período."}
            )
        return attrs
