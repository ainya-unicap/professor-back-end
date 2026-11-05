import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("relatorios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="relatorio",
            name="conclusao",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="relatorio",
            name="desenvolvimento",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="relatorio",
            name="introducao",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="relatorio",
            name="objetivo",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="relatorio",
            name="pdf",
            field=models.FileField(blank=True, upload_to="relatorios/pdf/"),
        ),
        migrations.AddField(
            model_name="relatorio",
            name="referencias",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="relatorio",
            name="nota",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=4,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(10),
                ],
            ),
        ),
        migrations.CreateModel(
            name="FotoRelatorio",
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
                ("imagem", models.ImageField(upload_to="relatorios/fotos/")),
                ("legenda", models.CharField(blank=True, max_length=200)),
                ("ordem", models.PositiveSmallIntegerField(default=0)),
                (
                    "relatorio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="fotos",
                        to="relatorios.relatorio",
                    ),
                ),
            ],
            options={
                "ordering": ["ordem", "id"],
            },
        ),
    ]
