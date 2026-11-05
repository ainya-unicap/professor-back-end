import secrets

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

ALFABETO_CODIGO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
TAMANHO_CODIGO = 6

validar_periodo = RegexValidator(
    r"^\d{4}\.[12]$",
    "Use o formato ano.semestre, por exemplo 2026.1.",
)


def gerar_codigo_convite():
    while True:
        codigo = "".join(secrets.choice(ALFABETO_CODIGO) for _ in range(TAMANHO_CODIGO))
        if not Turma.objects.filter(codigo_convite=codigo).exists():
            return codigo


class Turma(models.Model):
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="turmas",
    )
    nome = models.CharField(max_length=100)
    periodo = models.CharField(max_length=6, validators=[validar_periodo])
    instituicao = models.CharField(max_length=150)
    codigo_convite = models.CharField(max_length=TAMANHO_CODIGO, unique=True, editable=False)
    ativa = models.BooleanField(default=True)
    inicio_registros = models.DateField(null=True, blank=True)
    encerramento_registros = models.DateField(null=True, blank=True)
    limite_entrega = models.DateField(null=True, blank=True)
    prazo_correcao = models.DateField(null=True, blank=True)
    aceitar_atrasadas = models.BooleanField(default=False)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-periodo", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["professor", "nome", "periodo"],
                name="turma_unica_por_professor_e_periodo",
            )
        ]

    def __str__(self):
        return f"{self.nome} · {self.periodo}"

    def save(self, *args, **kwargs):
        if not self.codigo_convite:
            self.codigo_convite = gerar_codigo_convite()
        super().save(*args, **kwargs)

    def gerar_novo_codigo(self):
        self.codigo_convite = gerar_codigo_convite()
        self.save(update_fields=["codigo_convite"])

    @property
    def link_convite(self):
        return f"{settings.CONVITE_URL_BASE.rstrip('/')}/{self.codigo_convite}"


class Matricula(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name="matriculas")
    aluno = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="matriculas",
    )
    entrou_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["turma", "aluno"], name="aluno_unico_por_turma")
        ]

    def __str__(self):
        return f"{self.aluno} em {self.turma}"
