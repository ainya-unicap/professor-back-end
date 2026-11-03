from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import CadastroSerializer, LoginSerializer, resposta_autenticada


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class CadastroView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = CadastroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return Response(resposta_autenticada(usuario), status=status.HTTP_201_CREATED)
