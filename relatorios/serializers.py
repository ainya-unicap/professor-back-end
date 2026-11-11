from rest_framework import serializers

from .models import Relatorio


class RelatorioResumoSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    tem_pdf = serializers.SerializerMethodField()

    class Meta:
        model = Relatorio
        fields = ["id", "aluno", "planta", "entregue_em", "tem_pdf"]

    def get_aluno(self, relatorio):
        return relatorio.aluno.get_full_name() or relatorio.aluno.email

    def get_tem_pdf(self, relatorio):
        return bool(relatorio.pdf)
