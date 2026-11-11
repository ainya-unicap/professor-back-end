import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("turmas", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Relatorio",
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
                ("planta", models.CharField(max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[("rascunho", "Rascunho"), ("entregue", "Entregue")],
                        default="rascunho",
                        max_length=20,
                    ),
                ),
                ("pdf", models.FileField(blank=True, upload_to="relatorios/pdf/")),
                ("entregue_em", models.DateTimeField(blank=True, null=True)),
                (
                    "aluno",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="relatorios",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "turma",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="relatorios",
                        to="turmas.turma",
                    ),
                ),
            ],
            options={
                "ordering": ["-entregue_em"],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("turma", "aluno"),
                        name="relatorio_unico_por_aluno_e_turma",
                    )
                ],
            },
        ),
    ]
