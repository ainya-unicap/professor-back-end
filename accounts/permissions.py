from rest_framework.permissions import BasePermission


class EhProfessor(BasePermission):
    message = "Acesso exclusivo para professores."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.papel == "professor")
