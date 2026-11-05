import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from turmas.models import Matricula, Turma

from .models import FotoRelatorio, Relatorio

Usuario = get_user_model()
MIDIA_TESTE = tempfile.mkdtemp()


def criar_usuario(email, papel="professor", nome="Maria", sobrenome="Lima"):
    return Usuario.objects.create_user(
        username=email, email=email, password="canteiro-forte-2026", first_name=nome, last_name=sobrenome, papel=papel
    )


def imagem_png():
    arquivo = BytesIO()
    Image.new("RGB", (4, 4), "green").save(arquivo, "PNG")
    return ContentFile(arquivo.getvalue(), name="foto.png")


@override_settings(MEDIA_ROOT=MIDIA_TESTE)
class RelatorioTests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MIDIA_TESTE, ignore_errors=True)

    def setUp(self):
        self.professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(self.professor)
        self.turma = Turma.objects.create(
            professor=self.professor,
            nome="Turma A",
            periodo="2026.1",
            instituicao="UNICAP",
            prazo_correcao=timezone.localdate() + timedelta(days=10),
        )
        agora = timezone.now()
        self.relatorios = []
        for i, nome in enumerate(["Pedro", "Ana", "Bruno"]):
            aluno = criar_usuario(f"{nome}@t.com", papel="aluno", nome=nome, sobrenome="Silva")
            Matricula.objects.create(turma=self.turma, aluno=aluno)
            self.relatorios.append(
                Relatorio.objects.create(
                    turma=self.turma,
                    aluno=aluno,
                    planta="Camelo",
                    status="entregue",
                    entregue_em=agora - timedelta(days=10 - i),
                    introducao="Contexto",
                    objetivo="Objetivo",
                    desenvolvimento="Desenvolvimento",
                    conclusao="Conclusão",
                    referencias="Fontes",
                )
            )
        rascunho_aluno = criar_usuario("davi@t.com", papel="aluno", nome="Davi")
        self.rascunho = Relatorio.objects.create(turma=self.turma, aluno=rascunho_aluno, planta="Aruana")

    def url(self, relatorio, nome="relatorio"):
        return reverse(nome, args=[relatorio.pk])

    def test_detalhe_com_secoes_e_vizinhos(self):
        meio = self.relatorios[1]
        FotoRelatorio.objects.create(relatorio=meio, imagem=imagem_png(), legenda="Rebrota", ordem=1)
        resposta = self.client.get(self.url(meio))
        self.assertEqual(resposta.status_code, 200)
        dados = resposta.data
        self.assertEqual(dados["aluno"]["nome"], "Ana Silva")
        self.assertEqual(dados["turma"]["nome"], "Turma A")
        self.assertEqual(dados["introducao"], "Contexto")
        self.assertEqual(dados["fotos"][0]["legenda"], "Rebrota")
        self.assertFalse(dados["tem_pdf"])
        self.assertEqual(dados["anterior"], self.relatorios[0].pk)
        self.assertEqual(dados["proximo"], self.relatorios[2].pk)

    def test_primeiro_e_ultimo_nao_tem_vizinho(self):
        self.assertIsNone(self.client.get(self.url(self.relatorios[0])).data["anterior"])
        self.assertIsNone(self.client.get(self.url(self.relatorios[2])).data["proximo"])

    def test_rascunho_nao_aparece(self):
        self.assertEqual(self.client.get(self.url(self.rascunho)).status_code, 404)

    def test_relatorio_de_outro_professor_retorna_404(self):
        self.client.force_authenticate(criar_usuario("outro@t.com"))
        self.assertEqual(self.client.get(self.url(self.relatorios[0])).status_code, 404)

    def test_salvar_sem_concluir_mantem_aguardando(self):
        relatorio = self.relatorios[0]
        resposta = self.client.patch(
            self.url(relatorio, "relatorio_avaliacao"), {"nota": "8.5", "feedback": "Muito bom"}, format="json"
        )
        self.assertEqual(resposta.status_code, 200)
        relatorio.refresh_from_db()
        self.assertEqual(relatorio.nota, Decimal("8.5"))
        self.assertEqual(relatorio.status, "entregue")
        self.assertIsNone(relatorio.corrigido_em)

    def test_concluir_marca_como_corrigido(self):
        relatorio = self.relatorios[0]
        resposta = self.client.patch(
            self.url(relatorio, "relatorio_avaliacao"), {"nota": "9", "concluir": True}, format="json"
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.data["status"], "corrigido")
        relatorio.refresh_from_db()
        self.assertEqual(relatorio.status, "corrigido")
        self.assertIsNotNone(relatorio.corrigido_em)

    def test_concluir_sem_nota(self):
        resposta = self.client.patch(
            self.url(self.relatorios[0], "relatorio_avaliacao"), {"feedback": "ok", "concluir": True}, format="json"
        )
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("nota", resposta.data)

    def test_nota_fora_do_intervalo(self):
        for nota in ("11", "-1"):
            resposta = self.client.patch(
                self.url(self.relatorios[0], "relatorio_avaliacao"), {"nota": nota}, format="json"
            )
            self.assertEqual(resposta.status_code, 400)
            self.assertEqual(resposta.data["nota"], ["A nota vai de 0 a 10."])

    def test_pdf(self):
        relatorio = self.relatorios[0]
        self.assertEqual(self.client.get(self.url(relatorio, "relatorio_pdf")).status_code, 404)
        relatorio.pdf.save("r.pdf", ContentFile(b"%PDF-1.4 teste"))
        resposta = self.client.get(self.url(relatorio, "relatorio_pdf"))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "application/pdf")
        self.assertIn("attachment", resposta["Content-Disposition"])
        self.assertEqual(b"".join(resposta.streaming_content), b"%PDF-1.4 teste")

    def test_foto(self):
        relatorio = self.relatorios[0]
        foto = FotoRelatorio.objects.create(relatorio=relatorio, imagem=imagem_png())
        resposta = self.client.get(reverse("relatorio_foto", args=[relatorio.pk, foto.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta["Content-Type"], "image/png")

    def test_aluno_nao_acessa(self):
        self.client.force_authenticate(criar_usuario("aluno@t.com", papel="aluno"))
        self.assertEqual(self.client.get(self.url(self.relatorios[0])).status_code, 403)


class RelatoriosDaTurmaTests(APITestCase):
    def setUp(self):
        self.professor = criar_usuario("prof@teste.com")
        self.client.force_authenticate(self.professor)
        self.turma = Turma.objects.create(professor=self.professor, nome="Turma A", periodo="2026.1", instituicao="UNICAP")
        agora = timezone.now()
        dados = [("Pedro", "entregue", 1), ("Ana", "corrigido", 3), ("Bruno", "rascunho", None), ("Carla", "entregue", 2)]
        for nome, status, dias in dados:
            aluno = criar_usuario(f"{nome}@t.com", papel="aluno", nome=nome, sobrenome="Silva")
            Relatorio.objects.create(
                turma=self.turma,
                aluno=aluno,
                planta="Camelo",
                status=status,
                entregue_em=agora - timedelta(days=dias) if dias else None,
            )

    def test_lista_aguardando_primeiro_e_depois_do_mais_recente(self):
        resposta = self.client.get(reverse("relatorios_da_turma", args=[self.turma.pk]))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            [(r["aluno"], r["status"]) for r in resposta.data],
            [("Pedro Silva", "entregue"), ("Carla Silva", "entregue"), ("Ana Silva", "corrigido")],
        )
        self.assertFalse(resposta.data[0]["tem_pdf"])

    def test_turma_de_outro_professor(self):
        self.client.force_authenticate(criar_usuario("outro@t.com"))
        self.assertEqual(self.client.get(reverse("relatorios_da_turma", args=[self.turma.pk])).status_code, 404)
