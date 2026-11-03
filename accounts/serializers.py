from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        usuario = self.user
        data["usuario"] = {
            "id": usuario.id,
            "nome": usuario.get_full_name() or usuario.username,
            "email": usuario.email,
            "matricula": usuario.matricula,
            "papel": usuario.papel,
        }
        return data
