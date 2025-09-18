# hotel/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from .decorators import HospedeRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.exceptions import ValidationError

from .models import Quarto, Reserva
from .forms import QuartoForm, AlterarStatusReservaForm, BuscarQuartoForm
from .decorators import FuncionarioRequiredMixin  # Nosso mixin de permissão

# --- Mixin de Permissão ---


class HospedeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Garante que o usuário esteja logado E seja um hóspede.
    """

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_hospede


class FuncionarioRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Garante que o usuário esteja logado E seja um funcionário.
    Caso contrário, retorna um erro 403 (Forbidden).
    """

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_funcionario


# --- Página Inicial (View de Exemplo) ---


def home(request):
    return render(request, "hotel/home.html")


# --- Gestão de Quartos (CRUD) ---


class QuartoListView(FuncionarioRequiredMixin, ListView):
    model = Quarto
    template_name = "hotel/funcionario/quarto_list.html"
    context_object_name = "quartos"
    ordering = ["numero"]


class QuartoCreateView(FuncionarioRequiredMixin, CreateView):
    model = Quarto
    form_class = QuartoForm
    template_name = "hotel/funcionario/quarto_form.html"
    success_url = reverse_lazy("hotel:quarto_list")

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)
        context["titulo"] = "Adicionar Novo Quarto"
        return context


class QuartoUpdateView(FuncionarioRequiredMixin, UpdateView):
    model = Quarto
    form_class = QuartoForm
    template_name = "hotel/funcionario/quarto_form.html"
    success_url = reverse_lazy("hotel:quarto_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Editar Quarto Nº {self.object.numero}"
        return context


class QuartoDeleteView(FuncionarioRequiredMixin, DeleteView):
    model = Quarto
    template_name = "hotel/funcionario/quarto_confirm_delete.html"
    success_url = reverse_lazy("hotel:quarto_list")
    context_object_name = "quarto"


# --- Gestão de Reservas ---


class ReservaListViewFuncionario(FuncionarioRequiredMixin, ListView):
    model = Reserva
    template_name = "hotel/funcionario/reserva_list.html"
    context_object_name = "reservas"
    ordering = ["-data_checkin"]  # Mostra as reservas mais recentes primeiro


class ReservaUpdateStatusView(FuncionarioRequiredMixin, UpdateView):
    model = Reserva
    form_class = AlterarStatusReservaForm
    template_name = "hotel/funcionario/reserva_update_status.html"
    success_url = reverse_lazy("hotel:reserva_list_funcionario")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["titulo"] = f"Alterar Status da Reserva #{self.object.id}"
        return context


# --- Área do Hóspede: Realizar Reserva ---


class BuscarQuartoView(HospedeRequiredMixin, ListView):
    model = Quarto
    template_name = "hotel/hospede/buscar_quarto.html"
    context_object_name = "quartos_disponiveis"

    def get_queryset(self):
        """
        Este método é o núcleo da busca. Ele filtra os quartos com base nas datas.
        """
        form = BuscarQuartoForm(self.request.GET)
        if form.is_valid():
            checkin = form.cleaned_data["data_checkin"]
            checkout = form.cleaned_data["data_checkout"]

            # 1. Encontra os IDs dos quartos que JÁ ESTÃO reservados no período desejado.
            # Uma reserva conflita se:
            #    - seu check-in é antes do checkout da busca E
            #    - seu checkout é depois do check-in da busca
            quartos_ocupados_ids = Reserva.objects.filter(
                status=Reserva.StatusReserva.CONFIRMADO,
                data_checkin__lt=checkout,
                data_checkout__gt=checkin,
            ).values_list("quarto_id", flat=True)

            # 2. Retorna todos os quartos disponíveis que NÃO ESTÃO na lista de ocupados.
            return Quarto.objects.filter(disponivel=True).exclude(
                id__in=quartos_ocupados_ids
            )

        # Se o formulário não for válido ou não for submetido, não retorna nenhum quarto.
        return Quarto.objects.none()

    def get_context_data(self, **kwargs):
        """Adiciona o formulário de busca ao contexto do template."""
        context = super().get_context_data(**kwargs)
        # Passa os dados da busca (request.GET) para o formulário para que as datas
        # permaneçam nos campos após a busca.
        context["form"] = BuscarQuartoForm(self.request.GET or None)
        return context


def criar_reserva_view(request, quarto_id):
    """
    Processa a criação da reserva após o hóspede clicar em "Reservar".
    Esta é uma view baseada em função, pois não exibe um template, apenas processa e redireciona.
    """
    if not (request.user.is_authenticated and request.user.is_hospede):
        messages.error(request, "Acesso negado.")
        return redirect("hotel:home")

    quarto = get_object_or_404(Quarto, id=quarto_id)
    checkin_str = request.GET.get("checkin")
    checkout_str = request.GET.get("checkout")

    # Validação para garantir que as datas foram passadas pela URL
    if not (checkin_str and checkout_str):
        messages.error(request, "Datas de check-in e check-out são obrigatórias.")
        return redirect("hotel:buscar_quarto")

    reserva = Reserva(
        hospede=request.user,
        quarto=quarto,
        data_checkin=checkin_str,
        data_checkout=checkout_str,
    )

    try:
        # O método save() do modelo já chama o full_clean(), que executa as validações.
        reserva.save()
        messages.success(
            request, f"Sua reserva para o {quarto} foi confirmada com sucesso!"
        )
        return redirect("hotel:minhas_reservas")
    except ValidationError as e:
        # Se a validação falhar (ex: alguém reservou no último segundo), exibe o erro.
        # O 'e.message_dict' captura os erros de validação.
        error_message = next(iter(e.message_dict.values()))[0]
        messages.error(request, f"Não foi possível criar a reserva: {error_message}")
        return redirect("hotel:buscar_quarto")


# --- Área do Hóspede: Minhas Reservas ---


class MinhasReservasView(HospedeRequiredMixin, ListView):
    model = Reserva
    template_name = "hotel/hospede/minhas_reservas.html"
    context_object_name = "reservas"

    def get_queryset(self):
        """Retorna apenas as reservas pertencentes ao usuário logado."""
        return Reserva.objects.filter(hospede=self.request.user).order_by(
            "-data_checkin"
        )


def cancelar_reserva_view(request, pk):
    """Processa o cancelamento de uma reserva."""
    reserva = get_object_or_404(Reserva, pk=pk, hospede=request.user)

    # Regra de negócio: só pode cancelar reservas futuras e que estão confirmadas.
    if (
        reserva.data_checkin > timezone.now().date()
        and reserva.status == Reserva.StatusReserva.CONFIRMADO
    ):
        reserva.status = Reserva.StatusReserva.CANCELADO
        reserva.save()
        messages.success(request, "Sua reserva foi cancelada com sucesso.")
    else:
        messages.error(request, "Esta reserva não pode ser cancelada.")

    return redirect("hotel:minhas_reservas")
