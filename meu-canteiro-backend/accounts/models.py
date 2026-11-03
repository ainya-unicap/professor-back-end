from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    class Papel(models.TextChoices):
        PROFESSOR = "professor", "Professor"
        ALUNO = "aluno", "Aluno"

    email = models.EmailField(unique=True)
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    papel = models.CharField(max_length=20, choices=Papel.choices, default=Papel.ALUNO)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
