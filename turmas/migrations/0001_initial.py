
import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Turma",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nome", models.CharField(max_length=100)),
                (
                    "periodo",
                    models.CharField(
                        max_length=6,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^\\d{4}\\.[12]$",
                                "Use o formato ano.semestre, por exemplo 2026.1.",
                            )
                        ],
                    ),
                ),
                ("instituicao", models.CharField(max_length=150)),
                (
                    "codigo_convite",
                    models.CharField(editable=False, max_length=6, unique=True),
                ),
                ("ativa", models.BooleanField(default=True)),
                ("inicio_registros", models.DateField(blank=True, null=True)),
                ("encerramento_registros", models.DateField(blank=True, null=True)),
                ("limite_entrega", models.DateField(blank=True, null=True)),
                ("prazo_correcao", models.DateField(blank=True, null=True)),
                ("aceitar_atrasadas", models.BooleanField(default=False)),
                ("criada_em", models.DateTimeField(auto_now_add=True)),
                (
                    "professor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="turmas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-periodo", "nome"],
            },
        ),
        migrations.CreateModel(
            name="Matricula",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("entrou_em", models.DateTimeField(auto_now_add=True)),
                (
                    "aluno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matriculas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "turma",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="matriculas",
                        to="turmas.turma",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="turma",
            constraint=models.UniqueConstraint(
                fields=("professor", "nome", "periodo"),
                name="turma_unica_por_professor_e_periodo",
            ),
        ),
        migrations.AddConstraint(
            model_name="matricula",
            constraint=models.UniqueConstraint(
                fields=("turma", "aluno"), name="aluno_unico_por_turma"
            ),
        ),
    ]
