# hotel/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Quarto, Reserva


# Para exibir o campo 'tipo_usuario' no painel de admin para o Usuario
class CustomUserAdmin(UserAdmin):
    # Adiciona o campo 'tipo_usuario' aos campos exibidos na criação/edição
    fieldsets = UserAdmin.fieldsets + (
        ("Papel do Usuário", {"fields": ("tipo_usuario",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Papel do Usuário", {"fields": ("tipo_usuario",)}),
    )


# Registra os modelos para que apareçam na interface de admin
admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Quarto)
admin.site.register(Reserva)
