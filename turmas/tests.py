from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from relatorios.models import Relatorio

from .models import ALFABETO_CODIGO, TAMANHO_CODIGO, Matricula, Turma

Usuario = get_user_model()


def criar_usuario(email, papel="professor", nome="Maria", sobrenome="Lima"):
    return Usuario.objects.create_user(
        username=email,
        email=email,
        password="canteiro-forte-2026",
        first_name=nome,
        last_name=sobrenome,
        papel=papel,
    )


class TurmaTests(APITestCase):
    def setUp(self):
        self.professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(self.professor)
        self.url = reverse("turmas")
        self.dados = {"nome": " Turma   A ", "periodo": "2026.1", "instituicao": "UNICAP"}

    def test_cria_turma_com_codigo_de_convite(self):
        resposta = self.client.post(self.url, self.dados)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["nome"], "Turma A")
        self.assertEqual(resposta.data["alunos"], 0)
        codigo = resposta.data["codigo_convite"]
        self.assertEqual(len(codigo), TAMANHO_CODIGO)
        self.assertTrue(all(c in ALFABETO_CODIGO for c in codigo))
        self.assertEqual(Turma.objects.get().professor, self.professor)

    def test_codigos_sao_unicos(self):
        self.client.post(self.url, self.dados)
        self.client.post(self.url, {**self.dados, "nome": "Turma B"})
        codigos = set(Turma.objects.values_list("codigo_convite", flat=True))
        self.assertEqual(len(codigos), 2)

    def test_nao_permite_turma_repetida_no_mesmo_periodo(self):
        self.client.post(self.url, self.dados)
        resposta = self.client.post(self.url, {**self.dados, "nome": "turma a"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("nome", resposta.data)

    def test_permite_mesmo_nome_em_outro_periodo(self):
        self.client.post(self.url, self.dados)
        resposta = self.client.post(self.url, {**self.dados, "periodo": "2026.2"})
        self.assertEqual(resposta.status_code, 201)

    def test_periodo_invalido(self):
        resposta = self.client.post(self.url, {**self.dados, "periodo": "2026/1"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("periodo", resposta.data)

    def test_campos_obrigatorios(self):
        resposta = self.client.post(self.url, {})
        self.assertEqual(resposta.status_code, 400)
        for campo in ("nome", "periodo", "instituicao"):
            self.assertIn(campo, resposta.data)

    def test_lista_so_as_turmas_do_professor(self):
        outro = criar_usuario("outro@teste.com")
        Turma.objects.create(professor=outro, nome="Turma X", periodo="2026.1", instituicao="UNICAP")
        self.client.post(self.url, self.dados)
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([t["nome"] for t in resposta.data], ["Turma A"])

    def test_aluno_nao_acessa(self):
        self.client.force_authenticate(criar_usuario("aluno@teste.com", papel="aluno"))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.dados).status_code, 403)

    def test_sem_login_retorna_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)


class PainelTests(APITestCase):
    def setUp(self):
        self.professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(self.professor)
        self.url = reverse("painel")

    def test_painel_vazio(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertIsNone(resposta.data["periodo_atual"])
        self.assertEqual(
            resposta.data["resumo"],
            {
                "aguardando_correcao": 0,
                "turmas_com_pendencia": 0,
                "turmas_ativas": 0,
                "alunos": 0,
                "prazo_avaliacao": None,
            },
        )
        self.assertEqual(resposta.data["turmas"], [])
        self.assertEqual(resposta.data["aguardando"], [])

    def test_painel_com_dados(self):
        hoje = timezone.localdate()
        turma_a = Turma.objects.create(
            professor=self.professor,
            nome="Turma A",
            periodo="2026.1",
            instituicao="UNICAP",
            prazo_correcao=hoje + timedelta(days=10),
        )
        turma_b = Turma.objects.create(
            professor=self.professor,
            nome="Turma B",
            periodo="2026.1",
            instituicao="UNICAP",
            prazo_correcao=hoje + timedelta(days=3),
        )
        Turma.objects.create(
            professor=criar_usuario("outro@teste.com"),
            nome="Turma X",
            periodo="2026.1",
            instituicao="UNICAP",
        )
        agora = timezone.now()
        alunos = [criar_usuario(f"aluno{i}@teste.com", papel="aluno", nome=f"Aluno{i}", sobrenome="Silva") for i in range(4)]
        for aluno in alunos[:3]:
            Matricula.objects.create(turma=turma_a, aluno=aluno)
        Matricula.objects.create(turma=turma_b, aluno=alunos[3])
        Matricula.objects.create(turma=turma_b, aluno=alunos[0])

        Relatorio.objects.create(turma=turma_a, aluno=alunos[0], planta="Camelo", status="entregue", entregue_em=agora - timedelta(days=2))
        Relatorio.objects.create(turma=turma_a, aluno=alunos[1], planta="Aruana", status="corrigido", entregue_em=agora - timedelta(days=3))
        Relatorio.objects.create(turma=turma_a, aluno=alunos[2], planta="Camelo", status="rascunho")
        Relatorio.objects.create(turma=turma_b, aluno=alunos[3], planta="Amendoim Forrageiro", status="entregue", entregue_em=agora - timedelta(days=5))

        resposta = self.client.get(self.url)
        dados = resposta.data
        self.assertEqual(dados["periodo_atual"], "2026.1")
        self.assertEqual(dados["instituicao"], "UNICAP")
        self.assertEqual(dados["resumo"]["aguardando_correcao"], 2)
        self.assertEqual(dados["resumo"]["turmas_com_pendencia"], 2)
        self.assertEqual(dados["resumo"]["turmas_ativas"], 2)
        self.assertEqual(dados["resumo"]["alunos"], 4)
        self.assertEqual(dados["resumo"]["prazo_avaliacao"], hoje + timedelta(days=3))

        turma = next(t for t in dados["turmas"] if t["nome"] == "Turma A")
        self.assertEqual(turma["alunos"], 3)
        self.assertEqual(turma["relatorios_entregues"], 2)
        self.assertEqual(turma["aguardando_correcao"], 1)

        self.assertEqual(
            [(r["aluno"], r["planta"], r["turma"]) for r in dados["aguardando"]],
            [("Aluno3 Silva", "Amendoim Forrageiro", "Turma B"), ("Aluno0 Silva", "Camelo", "Turma A")],
        )

    def test_prazo_passado_nao_conta(self):
        Turma.objects.create(
            professor=self.professor,
            nome="Turma A",
            periodo="2026.1",
            instituicao="UNICAP",
            prazo_correcao=timezone.localdate() - timedelta(days=1),
        )
        resposta = self.client.get(self.url)
        self.assertIsNone(resposta.data["resumo"]["prazo_avaliacao"])

    def test_aluno_nao_acessa(self):
        self.client.force_authenticate(criar_usuario("aluno@teste.com", papel="aluno"))
        self.assertEqual(self.client.get(self.url).status_code, 403)


class TurmaDetalheTests(APITestCase):
    def setUp(self):
        self.professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(self.professor)
        self.turma = Turma.objects.create(
            professor=self.professor, nome="Turma A", periodo="2026.1", instituicao="UNICAP"
        )
        self.url = reverse("turma", args=[self.turma.pk])

    def test_detalhe_com_convite_e_alunos(self):
        ana = criar_usuario("ana@t.com", papel="aluno", nome="Ana", sobrenome="Souza")
        bruno = criar_usuario("bruno@t.com", papel="aluno", nome="Bruno", sobrenome="Lima")
        carla = criar_usuario("carla@t.com", papel="aluno", nome="Carla", sobrenome="Reis")
        davi = criar_usuario("davi@t.com", papel="aluno", nome="Davi", sobrenome="Melo")
        for aluno in (ana, bruno, carla, davi):
            Matricula.objects.create(turma=self.turma, aluno=aluno)
        Relatorio.objects.create(turma=self.turma, aluno=bruno, planta="Aruana", status="corrigido")
        entregue = Relatorio.objects.create(turma=self.turma, aluno=carla, planta="Camelo", status="entregue")
        Relatorio.objects.create(turma=self.turma, aluno=davi, planta="Camelo", status="rascunho")

        with self.settings(CONVITE_URL_BASE="https://alunos.exemplo/convite/"):
            resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            resposta.data["link_convite"],
            f"https://alunos.exemplo/convite/{self.turma.codigo_convite}",
        )
        self.assertEqual(resposta.data["alunos"], 4)
        self.assertEqual(
            [(a["nome"], a["status"], a["relatorio_id"]) for a in resposta.data["alunos_lista"]],
            [
                ("Carla Reis", "entregue", entregue.id),
                ("Bruno Lima", "corrigido", Relatorio.objects.get(aluno=bruno).id),
                ("Ana Souza", "sem_relatorio", None),
                ("Davi Melo", "sem_relatorio", None),
            ],
        )

    def test_turma_de_outro_professor_retorna_404(self):
        outra = Turma.objects.create(
            professor=criar_usuario("outro@t.com"), nome="Turma X", periodo="2026.1", instituicao="UNICAP"
        )
        self.assertEqual(self.client.get(reverse("turma", args=[outra.pk])).status_code, 404)
        self.assertEqual(self.client.patch(reverse("turma_prazos", args=[outra.pk]), {}).status_code, 404)
        self.assertEqual(self.client.post(reverse("turma_novo_codigo", args=[outra.pk])).status_code, 404)

    def test_salva_prazos(self):
        resposta = self.client.patch(
            reverse("turma_prazos", args=[self.turma.pk]),
            {
                "inicio_registros": "2026-03-02",
                "encerramento_registros": "2026-06-05",
                "limite_entrega": "2026-06-12",
                "prazo_correcao": "2026-06-26",
                "aceitar_atrasadas": True,
            },
            format="json",
        )
        self.assertEqual(resposta.status_code, 200)
        self.turma.refresh_from_db()
        self.assertEqual(str(self.turma.prazo_correcao), "2026-06-26")
        self.assertTrue(self.turma.aceitar_atrasadas)

    def test_prazos_fora_de_ordem(self):
        resposta = self.client.patch(
            reverse("turma_prazos", args=[self.turma.pk]),
            {"inicio_registros": "2026-06-10", "encerramento_registros": "2026-06-05"},
            format="json",
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("encerramento_registros", resposta.data)

    def test_prazos_podem_ficar_vazios(self):
        resposta = self.client.patch(
            reverse("turma_prazos", args=[self.turma.pk]),
            {"inicio_registros": None, "prazo_correcao": "2026-06-26"},
            format="json",
        )
        self.assertEqual(resposta.status_code, 200)

    def test_gera_novo_codigo(self):
        antigo = self.turma.codigo_convite
        resposta = self.client.post(reverse("turma_novo_codigo", args=[self.turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.turma.refresh_from_db()
        self.assertNotEqual(self.turma.codigo_convite, antigo)
        self.assertEqual(resposta.data["codigo_convite"], self.turma.codigo_convite)
        self.assertTrue(resposta.data["link_convite"].endswith(self.turma.codigo_convite))

    def test_aluno_nao_acessa(self):
        self.client.force_authenticate(criar_usuario("aluno@t.com", papel="aluno"))
        self.assertEqual(self.client.get(self.url).status_code, 403)


class PendentesTests(APITestCase):
    def test_conta_so_os_entregues_das_turmas_do_professor(self):
        professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(professor)
        turma = Turma.objects.create(professor=professor, nome="Turma A", periodo="2026.1", instituicao="UNICAP")
        outra = Turma.objects.create(professor=criar_usuario("o@t.com"), nome="X", periodo="2026.1", instituicao="U")
        for i, (t, status) in enumerate([(turma, "entregue"), (turma, "entregue"), (turma, "corrigido"), (outra, "entregue")]):
            aluno = criar_usuario(f"a{i}@t.com", papel="aluno")
            Relatorio.objects.create(turma=t, aluno=aluno, planta="Camelo", status=status)
        resposta = self.client.get(reverse("pendentes"))
        self.assertEqual(resposta.data, {"aguardando_correcao": 2})
