from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from turmas.models import Turma


class Relatorio(models.Model):
    class Status(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        ENTREGUE = "entregue", "Aguardando correção"
        CORRIGIDO = "corrigido", "Corrigido"

    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="relatorios")
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="relatorios",
    )
    planta = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RASCUNHO)
    introducao = models.TextField(blank=True)
    objetivo = models.TextField(blank=True)
    desenvolvimento = models.TextField(blank=True)
    conclusao = models.TextField(blank=True)
    referencias = models.TextField(blank=True)
    pdf = models.FileField(upload_to="relatorios/pdf/", blank=True)
    entregue_em = models.DateTimeField(null=True, blank=True)
    nota = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    feedback = models.TextField(blank=True)
    corrigido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["entregue_em"]
        constraints = [
            models.UniqueConstraint(fields=["turma", "aluno"], name="relatorio_unico_por_aluno_e_turma")
        ]

    def __str__(self):
        return f"{self.aluno} · {self.planta} · {self.turma}"


class FotoRelatorio(models.Model):
    relatorio = models.ForeignKey(Relatorio, on_delete=models.CASCADE, related_name="fotos")
    imagem = models.ImageField(upload_to="relatorios/fotos/")
    legenda = models.CharField(max_length=200, blank=True)
    ordem = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["ordem", "id"]

    def __str__(self):
        return self.legenda or f"Foto {self.pk}"
