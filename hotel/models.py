# hotel/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


# --- Modelo de Usuário Customizado ---


class Usuario(AbstractUser):
    """
    Modelo de usuário customizado com os campos padrão (username, email, password)
    e um campo adicional para definir o papel do usuário.
    """

    class Tipo(models.TextChoices):
        HOSPEDE = "HOSPEDE", "Hóspede"
        FUNCIONARIO = "FUNCIONARIO", "Funcionário"

    tipo_usuario = models.CharField(
        max_length=20,
        choices=Tipo.choices,
        default=Tipo.HOSPEDE,
        help_text="Define o papel do usuário no sistema (Hóspede ou Funcionário).",
    )

    @property
    def is_hospede(self):
        return self.tipo_usuario == self.Tipo.HOSPEDE

    @property
    def is_funcionario(self):
        return self.tipo_usuario == self.Tipo.FUNCIONARIO


# --- Modelo de Quarto ---


class Quarto(models.Model):
    """
    Representa um quarto do hotel com suas características básicas.
    """

    class TipoQuarto(models.TextChoices):
        SOLTEIRO = "SOLTEIRO", "Solteiro"
        CASAL = "CASAL", "Casal"
        LUXO = "LUXO", "Luxo"

    numero = models.PositiveIntegerField(
        unique=True, help_text="Número único que identifica o quarto."
    )
    tipo = models.CharField(
        max_length=20,
        choices=TipoQuarto.choices,
        help_text="Categoria do quarto (Solteiro, Casal, etc.).",
    )
    disponivel = models.BooleanField(
        default=True,
        help_text="Indica se o quarto está disponível para novas reservas.",
    )

    def __str__(self):
        return f"Quarto Nº {self.numero} ({self.get_tipo_display()})"


# --- Modelo de Reserva ---


class Reserva(models.Model):
    """
    Representa a reserva de um quarto por um hóspede em um determinado período.
    """

    class StatusReserva(models.TextChoices):
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        CANCELADO = "CANCELADO", "Cancelado"
        CONCLUIDO = "CONCLUIDO", "Concluído"

    hospede = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservas",
        limit_choices_to={"tipo_usuario": Usuario.Tipo.HOSPEDE},
        help_text="O hóspede que realizou a reserva.",
    )
    quarto = models.ForeignKey(
        Quarto,
        on_delete=models.CASCADE,
        related_name="reservas",
        help_text="O quarto que foi reservado.",
    )
    data_checkin = models.DateField(help_text="Data de início da hospedagem.")
    data_checkout = models.DateField(help_text="Data de término da hospedagem.")
    data_criacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, choices=StatusReserva.choices, default=StatusReserva.CONFIRMADO
    )

    def __str__(self):
        return f"Reserva de {self.hospede.username} para o Quarto {self.quarto.numero} ({self.data_checkin.strftime('%d/%m/%Y')})"

    def clean(self):
        """
        Validações de negócio executadas antes de salvar o modelo.
        """
        # 1. Garante que a data de checkout seja posterior à de check-in.
        if self.data_checkout <= self.data_checkin:
            raise ValidationError(
                "A data de checkout deve ser posterior à data de check-in."
            )

        # 2. Garante que a data de check-in não seja no passado para novas reservas.
        if self.pk is None and self.data_checkin < timezone.now().date():
            raise ValidationError(
                "Não é possível criar uma reserva com data de check-in no passado."
            )

        # 3. Verifica conflitos de datas com outras reservas CONFIRMADAS para o mesmo quarto.
        reservas_conflitantes = Reserva.objects.filter(
            quarto=self.quarto,
            status=self.StatusReserva.CONFIRMADO,
            data_checkin__lt=self.data_checkout,
            data_checkout__gt=self.data_checkin,
        ).exclude(pk=self.pk)

        if reservas_conflitantes.exists():
            raise ValidationError(
                f"O Quarto {self.quarto.numero} já está reservado neste período."
            )

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para garantir que as validações do clean()
        sejam sempre executadas.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def pode_cancelar(self):
        """
        Retorna True se a reserva puder ser cancelada pelo hóspede.
        Regra: A data de check-in deve ser no futuro e o status deve ser 'Confirmado'.
        """
        return (
            self.data_checkin > timezone.now().date()
            and self.status == self.StatusReserva.CONFIRMADO
        )
