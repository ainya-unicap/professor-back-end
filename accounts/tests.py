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
