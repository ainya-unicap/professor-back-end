import shutil
import tempfile
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from turmas.models import Turma

from .models import Relatorio

Usuario = get_user_model()
MIDIA_TESTE = tempfile.mkdtemp()


def criar_usuario(email, papel="professor", nome="Maria", sobrenome="Lima"):
    return Usuario.objects.create_user(
        username=email, email=email, password="canteiro-forte-2026", first_name=nome, last_name=sobrenome, papel=papel
    )


@override_settings(MEDIA_ROOT=MIDIA_TESTE)
class RelatoriosTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MIDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(self.professor)
        self.turma = Turma.objects.create(professor=self.professor, nome="Turma A", periodo="2026.1", instituicao="UNICAP")
        agora = timezone.now()
        self.relatorios = {}
        for nome, status, dias in [("Pedro", "entregue", 1), ("Ana", "entregue", 3), ("Bruno", "rascunho", None)]:
            aluno = criar_usuario(f"{nome}@t.com", papel="aluno", nome=nome, sobrenome="Sá")
            self.relatorios[nome] = Relatorio.objects.create(
                turma=self.turma,
                aluno=aluno,
                planta="Camelo",
                status=status,
                entregue_em=agora - timedelta(days=dias) if dias else None,
            )

    def test_lista_os_entregues_do_mais_recente(self):
        resposta = self.client.get(reverse("relatorios_da_turma", args=[self.turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual([r["aluno"] for r in resposta.data], ["Pedro Sá", "Ana Sá"])
        self.assertEqual(resposta.data[0]["planta"], "Camelo")
        self.assertFalse(resposta.data[0]["tem_pdf"])

    def test_turma_de_outro_professor(self):
        self.client.force_authenticate(criar_usuario("outro@t.com"))
        self.assertEqual(self.client.get(reverse("relatorios_da_turma", args=[self.turma.pk])).status_code, 404)

    def test_baixa_o_pdf(self):
        relatorio = self.relatorios["Pedro"]
        url = reverse("relatorio_pdf", args=[relatorio.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        relatorio.pdf.save("r.pdf", ContentFile(b"%PDF-1.4 teste"))
        resposta = self.client.get(url)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertIn('filename="relatorio-pedro-sa.pdf"', resposta["Content-Disposition"])
        self.assertEqual(b"".join(resposta.streaming_content), b"%PDF-1.4 teste")

    def test_pdf_de_rascunho_nao_e_acessivel(self):
        relatorio = self.relatorios["Bruno"]
        relatorio.pdf.save("r.pdf", ContentFile(b"%PDF"))
        self.assertEqual(self.client.get(reverse("relatorio_pdf", args=[relatorio.pk])).status_code, 404)

    def test_pdf_de_outro_professor(self):
        self.client.force_authenticate(criar_usuario("outro@t.com"))
        self.assertEqual(self.client.get(reverse("relatorio_pdf", args=[self.relatorios["Pedro"].pk])).status_code, 404)

    def test_aluno_nao_acessa(self):
        self.client.force_authenticate(criar_usuario("aluno@t.com", papel="aluno"))
        self.assertEqual(self.client.get(reverse("relatorios_da_turma", args=[self.turma.pk])).status_code, 403)
