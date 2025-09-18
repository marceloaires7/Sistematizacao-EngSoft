# hotel/forms.py

from django import forms
from django.utils import timezone
from .models import Usuario, Quarto, Reserva

# --- 1. Formulário de Cadastro (django-allauth) ---
# Este formulário adiciona o campo 'tipo_usuario' à tela de registro padrão.


class CustomSignupForm(forms.Form):
    """
    Formulário de cadastro customizado para permitir que o usuário escolha
    seu papel (Hóspede ou Funcionário) no momento do registro.
    """

    tipo_usuario = forms.ChoiceField(
        choices=Usuario.Tipo.choices,
        required=True,
        label="Eu quero me cadastrar como",
        widget=forms.RadioSelect,  # Fica mais intuitivo que um dropdown
    )

    def signup(self, request, user):
        """
        Este método é chamado pelo django-allauth após o cadastro básico.
        Ele pega o dado do nosso campo customizado e o salva no objeto 'user'.
        """
        user.tipo_usuario = self.cleaned_data["tipo_usuario"]
        user.save()


# --- 2. Formulário para Gestão de Quartos (Painel do Funcionário) ---
# Usa ModelForm para criar um formulário diretamente a partir do modelo Quarto.


class QuartoForm(forms.ModelForm):
    """
    Formulário para criar e editar Quartos.
    """

    class Meta:
        model = Quarto
        fields = ["numero", "tipo", "disponivel"]
        labels = {
            "numero": "Número do Quarto",
            "tipo": "Tipo de Quarto",
            "disponivel": "Disponível para novas reservas",
        }
        help_texts = {
            "disponivel": "Desmarque esta opção para manutenções ou outras indisponibilidades."
        }


# --- 3. Formulário para Alterar Status da Reserva (Painel do Funcionário) ---


class AlterarStatusReservaForm(forms.ModelForm):
    """
    Formulário específico para o funcionário poder alterar o status de uma reserva.
    """

    class Meta:
        model = Reserva
        fields = ["status"]
        labels = {"status": "Novo Status da Reserva"}


# --- 4. Formulário de Busca de Quartos (Área do Hóspede) ---


class BuscarQuartoForm(forms.Form):
    """
    Formulário para o hóspede inserir as datas de check-in e check-out
    e encontrar quartos disponíveis.
    """

    data_checkin = forms.DateField(
        label="Data de Check-in",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    data_checkout = forms.DateField(
        label="Data de Check-out",
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )

    def clean_data_checkin(self):
        """Validação específica para o campo data_checkin."""
        data = self.cleaned_data["data_checkin"]
        if data < timezone.now().date():
            raise forms.ValidationError("A data de check-in não pode ser no passado.")
        return data

    def clean(self):
        """Validação que compara os dois campos (check-in e check-out)."""
        cleaned_data = super().clean()
        checkin = cleaned_data.get("data_checkin")
        checkout = cleaned_data.get("data_checkout")

        if checkin and checkout:
            if checkout <= checkin:
                raise forms.ValidationError(
                    "A data de checkout deve ser sempre posterior à data de check-in."
                )
        return cleaned_data
