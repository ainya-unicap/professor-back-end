from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

Usuario = get_user_model()


def dados_usuario(usuario):
    return {
        "id": usuario.id,
        "nome": usuario.get_full_name() or usuario.username,
        "email": usuario.email,
        "matricula": usuario.matricula,
        "papel": usuario.papel,
    }


def resposta_autenticada(usuario):
    refresh = RefreshToken.for_user(usuario)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "usuario": dados_usuario(usuario),
    }


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["usuario"] = dados_usuario(self.user)
        return data


class CadastroSerializer(serializers.Serializer):
    nome = serializers.CharField(max_length=150, trim_whitespace=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_nome(self, valor):
        nome = " ".join(valor.split())
        if len(nome.split()) < 2:
            raise serializers.ValidationError("Informe nome e sobrenome.")
        return nome

    def validate_email(self, valor):
        email = valor.strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def validate(self, attrs):
        primeiro, _, resto = attrs["nome"].partition(" ")
        candidato = Usuario(
            username=attrs["email"],
            email=attrs["email"],
            first_name=primeiro,
            last_name=resto,
        )
        try:
            validate_password(attrs["password"], user=candidato)
        except DjangoValidationError as erro:
            raise serializers.ValidationError({"password": list(erro.messages)})
        attrs["first_name"] = primeiro
        attrs["last_name"] = resto
        return attrs

    def create(self, validated_data):
        return Usuario.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            papel=Usuario.Papel.PROFESSOR,
        )
