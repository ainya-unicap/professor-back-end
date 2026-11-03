from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase


class LoginTests(APITestCase):
    def setUp(self):
        self.professor = get_user_model().objects.create_user(
            username="ana",
            email="ana@unicap.br",
            password="senha-forte-123",
            first_name="Ana",
            last_name="Souza",
            matricula="0000015638",
            papel="professor",
        )

    def test_login_retorna_tokens_e_usuario(self):
        resposta = self.client.post(
            reverse("login"),
            {"email": "ana@unicap.br", "password": "senha-forte-123"},
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("access", resposta.data)
        self.assertIn("refresh", resposta.data)
        self.assertEqual(resposta.data["usuario"]["nome"], "Ana Souza")
        self.assertEqual(resposta.data["usuario"]["papel"], "professor")

    def test_login_com_senha_errada_retorna_401(self):
        resposta = self.client.post(
            reverse("login"),
            {"email": "ana@unicap.br", "password": "errada"},
        )
        self.assertEqual(resposta.status_code, 401)


class CadastroTests(APITestCase):
    def setUp(self):
        self.url = reverse("cadastro")
        self.dados = {
            "nome": "  Ana   Souza Lima ",
            "email": "Ana@Unicap.br",
            "password": "canteiro-forte-2026",
        }

    def test_cadastro_cria_professor_e_retorna_tokens(self):
        resposta = self.client.post(self.url, self.dados)
        self.assertEqual(resposta.status_code, 201)
        self.assertIn("access", resposta.data)
        self.assertIn("refresh", resposta.data)
        self.assertEqual(resposta.data["usuario"]["nome"], "Ana Souza Lima")
        self.assertEqual(resposta.data["usuario"]["email"], "ana@unicap.br")
        self.assertEqual(resposta.data["usuario"]["papel"], "professor")

        usuario = get_user_model().objects.get(email="ana@unicap.br")
        self.assertEqual(usuario.first_name, "Ana")
        self.assertEqual(usuario.last_name, "Souza Lima")
        self.assertTrue(usuario.check_password("canteiro-forte-2026"))

    def test_professor_cadastrado_consegue_fazer_login(self):
        self.client.post(self.url, self.dados)
        resposta = self.client.post(
            reverse("login"),
            {"email": "ana@unicap.br", "password": "canteiro-forte-2026"},
        )
        self.assertEqual(resposta.status_code, 200)

    def test_email_repetido_retorna_400(self):
        self.client.post(self.url, self.dados)
        resposta = self.client.post(self.url, {**self.dados, "email": "ANA@unicap.br"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("email", resposta.data)

    def test_nome_sem_sobrenome_retorna_400(self):
        resposta = self.client.post(self.url, {**self.dados, "nome": "Ana"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("nome", resposta.data)

    def test_senha_fraca_retorna_400(self):
        resposta = self.client.post(self.url, {**self.dados, "password": "12345678"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("password", resposta.data)
        self.assertFalse(get_user_model().objects.filter(email="ana@unicap.br").exists())

    def test_campos_obrigatorios(self):
        resposta = self.client.post(self.url, {})
        self.assertEqual(resposta.status_code, 400)
        for campo in ("nome", "email", "password"):
            self.assertIn(campo, resposta.data)
