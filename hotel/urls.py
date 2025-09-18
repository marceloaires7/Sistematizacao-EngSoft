# hotel/urls.py (arquivo completo e atualizado)

from django.urls import path
from . import views

app_name = "hotel"

urlpatterns = [
    # URL da página inicial
    path("", views.home, name="home"),
    # --- URLs do Painel do Funcionário ---
    path("painel/quartos/", views.QuartoListView.as_view(), name="quarto_list"),
    path(
        "painel/quartos/novo/", views.QuartoCreateView.as_view(), name="quarto_create"
    ),
    path(
        "painel/quartos/<int:pk>/editar/",
        views.QuartoUpdateView.as_view(),
        name="quarto_update",
    ),
    path(
        "painel/quartos/<int:pk>/excluir/",
        views.QuartoDeleteView.as_view(),
        name="quarto_delete",
    ),
    path(
        "painel/reservas/",
        views.ReservaListViewFuncionario.as_view(),
        name="reserva_list_funcionario",
    ),
    path(
        "painel/reservas/<int:pk>/status/",
        views.ReservaUpdateStatusView.as_view(),
        name="reserva_update_status",
    ),
    # --- URLs da Área do Hóspede (NOVAS) ---
    path("hospede/buscar/", views.BuscarQuartoView.as_view(), name="buscar_quarto"),
    path(
        "hospede/reservar/<int:quarto_id>/",
        views.criar_reserva_view,
        name="criar_reserva",
    ),
    path(
        "hospede/minhas-reservas/",
        views.MinhasReservasView.as_view(),
        name="minhas_reservas",
    ),
    path(
        "hospede/minhas-reservas/<int:pk>/cancelar/",
        views.cancelar_reserva_view,
        name="cancelar_reserva",
    ),
]
