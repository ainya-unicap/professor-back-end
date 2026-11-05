from rest_framework import serializers

from relatorios.models import Relatorio

from .models import Turma


class TurmaSerializer(serializers.ModelSerializer):
    alunos = serializers.SerializerMethodField()
    relatorios_entregues = serializers.SerializerMethodField()
    aguardando_correcao = serializers.SerializerMethodField()

    class Meta:
        model = Turma
        fields = [
            "id",
            "nome",
            "periodo",
            "instituicao",
            "codigo_convite",
            "ativa",
            "alunos",
            "relatorios_entregues",
            "aguardando_correcao",
            "inicio_registros",
            "encerramento_registros",
            "limite_entrega",
            "prazo_correcao",
            "aceitar_atrasadas",
        ]
        read_only_fields = [
            "codigo_convite",
            "ativa",
            "inicio_registros",
            "encerramento_registros",
            "limite_entrega",
            "prazo_correcao",
            "aceitar_atrasadas",
        ]
        validators = []

    def get_alunos(self, turma):
        return getattr(turma, "total_alunos", 0)

    def get_relatorios_entregues(self, turma):
        return getattr(turma, "total_entregues", 0)

    def get_aguardando_correcao(self, turma):
        return getattr(turma, "total_pendentes", 0)

    def validate_nome(self, valor):
        return " ".join(valor.split())

    def validate_instituicao(self, valor):
        return " ".join(valor.split())

    def validate(self, attrs):
        professor = self.context["request"].user
        nome = attrs.get("nome", getattr(self.instance, "nome", None))
        periodo = attrs.get("periodo", getattr(self.instance, "periodo", None))
        repetidas = Turma.objects.filter(professor=professor, nome__iexact=nome, periodo=periodo)
        if self.instance:
            repetidas = repetidas.exclude(pk=self.instance.pk)
        if repetidas.exists():
            raise serializers.ValidationError(
                {"nome": "Você já tem uma turma com esse nome neste período."}
            )
        return attrs


class RelatorioPendenteSerializer(serializers.ModelSerializer):
    aluno = serializers.SerializerMethodField()
    turma = serializers.CharField(source="turma.nome")

    class Meta:
        model = Relatorio
        fields = ["id", "aluno", "planta", "turma", "entregue_em"]

    def get_aluno(self, relatorio):
        return relatorio.aluno.get_full_name() or relatorio.aluno.email


class TurmaDetalheSerializer(TurmaSerializer):
    link_convite = serializers.CharField(read_only=True)
    alunos_lista = serializers.SerializerMethodField()

    class Meta(TurmaSerializer.Meta):
        fields = TurmaSerializer.Meta.fields + ["link_convite", "alunos_lista"]

    def get_alunos_lista(self, turma):
        relatorios = {r.aluno_id: r for r in turma.relatorios.all()}
        ordem_status = {"entregue": 0, "corrigido": 1, "sem_relatorio": 2}
        alunos = []
        for matricula in turma.matriculas.select_related("aluno"):
            aluno = matricula.aluno
            relatorio = relatorios.get(aluno.id)
            if relatorio and relatorio.status != Relatorio.Status.RASCUNHO:
                status, relatorio_id = relatorio.status, relatorio.id
            else:
                status, relatorio_id = "sem_relatorio", None
            alunos.append(
                {
                    "id": aluno.id,
                    "nome": aluno.get_full_name() or aluno.email,
                    "status": status,
                    "relatorio_id": relatorio_id,
                }
            )
        alunos.sort(key=lambda a: (ordem_status[a["status"]], a["nome"].lower()))
        return alunos


class PrazosSerializer(serializers.ModelSerializer):
    ORDEM = [
        ("inicio_registros", "Início dos registros"),
        ("encerramento_registros", "Encerramento dos registros"),
        ("limite_entrega", "Limite de entrega"),
        ("prazo_correcao", "Prazo de correção"),
    ]

    class Meta:
        model = Turma
        fields = [
            "inicio_registros",
            "encerramento_registros",
            "limite_entrega",
            "prazo_correcao",
            "aceitar_atrasadas",
        ]

    def validate(self, attrs):
        datas = [
            (campo, rotulo, attrs.get(campo, getattr(self.instance, campo, None)))
            for campo, rotulo in self.ORDEM
        ]
        anterior = None
        erros = {}
        for campo, rotulo, valor in datas:
            if valor is None:
                continue
            if anterior and valor < anterior[2]:
                erros[campo] = f"{rotulo} não pode ser antes de: {anterior[1].lower()}."
            anterior = (campo, rotulo, valor)
        if erros:
            raise serializers.ValidationError(erros)
        return attrs
