from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import CadastroView, LoginView

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
