from django.conf import settings
from django.db import models

from turmas.models import Turma


class Relatorio(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENTREGUE = "entregue", "Entregue"

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="relatorios")
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="relatorios",
    )
    planta = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    pdf = models.FileField(upload_to="relatorios/pdf/", blank=True)
    entregue_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-entregue_em"]
        constraints = [
            models.UniqueConstraint(fields=["turma", "aluno"], name="relatorio_unico_por_aluno_e_turma")
        ]

    def __str__(self):
        return f"{self.aluno} · {self.planta} · {self.turma}"
