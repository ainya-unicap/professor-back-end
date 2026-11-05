from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ["email", "first_name", "last_name", "papel", "matricula", "is_staff"]
    list_filter = ["papel", "is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name", "matricula"]
    fieldsets = UserAdmin.fieldsets + (("Forrageia", {"fields": ("papel", "matricula")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Forrageia", {"fields": ("email", "papel", "matricula")}),)
