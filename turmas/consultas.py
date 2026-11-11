from django.db.models import Count, Q

from relatorios.models import Relatorio

from .models import Turma


def turmas_do_professor(professor):
    return Turma.objects.filter(professor=professor).annotate(
        total_alunos=Count("matriculas", distinct=True),
        total_entregues=Count(
            "relatorios",
            filter=Q(relatorios__status=Relatorio.Status.ENTREGUE),
            distinct=True,
        ),
    )
