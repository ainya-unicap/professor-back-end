from django.contrib.auth import get_user_model
from django.urls import reverse
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

    def test_cria_turma_com_codigo_e_link_de_convite(self):
        with self.settings(CONVITE_URL_BASE="https://alunos.exemplo/convite/"):
            resposta = self.client.post(self.url, self.dados)
        self.assertEqual(resposta.status_code, 201)
        self.assertEqual(resposta.data["nome"], "Turma A")
        self.assertEqual(resposta.data["alunos"], 0)
        codigo = resposta.data["codigo_convite"]
        self.assertEqual(len(codigo), TAMANHO_CODIGO)
        self.assertTrue(all(c in ALFABETO_CODIGO for c in codigo))
        self.assertEqual(resposta.data["link_convite"], f"https://alunos.exemplo/convite/{codigo}")
        self.assertEqual(Turma.objects.get().professor, self.professor)

    def test_codigos_sao_unicos(self):
        self.client.post(self.url, self.dados)
        self.client.post(self.url, {**self.dados, "nome": "Turma B"})
        self.assertEqual(len(set(Turma.objects.values_list("codigo_convite", flat=True))), 2)

    def test_nao_permite_turma_repetida_no_mesmo_periodo(self):
        self.client.post(self.url, self.dados)
        resposta = self.client.post(self.url, {**self.dados, "nome": "turma a"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("nome", resposta.data)

    def test_permite_mesmo_nome_em_outro_periodo(self):
        self.client.post(self.url, self.dados)
        self.assertEqual(self.client.post(self.url, {**self.dados, "periodo": "2026.2"}).status_code, 201)

    def test_periodo_invalido(self):
        resposta = self.client.post(self.url, {**self.dados, "periodo": "2026/1"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("periodo", resposta.data)

    def test_campos_obrigatorios(self):
        resposta = self.client.post(self.url, {})
        self.assertEqual(resposta.status_code, 400)
        for campo in ("nome", "periodo", "instituicao"):
            self.assertIn(campo, resposta.data)

    def test_lista_so_as_turmas_do_professor_com_contagens(self):
        outro = criar_usuario("outro@teste.com")
        Turma.objects.create(professor=outro, nome="Turma X", periodo="2026.1", instituicao="UNICAP")
        turma = Turma.objects.create(professor=self.professor, nome="Turma A", periodo="2026.1", instituicao="UNICAP")
        for i, status in enumerate(["entregue", "entregue", "rascunho", None]):
            aluno = criar_usuario(f"a{i}@t.com", papel="aluno")
            Matricula.objects.create(turma=turma, aluno=aluno)
            if status:
                Relatorio.objects.create(turma=turma, aluno=aluno, planta="Camelo", status=status)

        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data), 1)
        self.assertEqual(resposta.data[0]["alunos"], 4)
        self.assertEqual(resposta.data[0]["relatorios_entregues"], 2)

    def test_detalhe(self):
        turma = Turma.objects.create(professor=self.professor, nome="Turma A", periodo="2026.1", instituicao="UNICAP")
        resposta = self.client.get(reverse("turma", args=[turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["codigo_convite"], turma.codigo_convite)

    def test_detalhe_de_turma_de_outro_professor(self):
        turma = Turma.objects.create(
            professor=criar_usuario("outro@t.com"), nome="Turma X", periodo="2026.1", instituicao="UNICAP"
        )
        self.assertEqual(self.client.get(reverse("turma", args=[turma.pk])).status_code, 404)

    def test_aluno_nao_acessa(self):
        self.client.force_authenticate(criar_usuario("aluno@teste.com", papel="aluno"))
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.dados).status_code, 403)

    def test_sem_login_retorna_401(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(self.url).status_code, 401)
