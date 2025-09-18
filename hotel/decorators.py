# hotel/decorators.py

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied


def funcionario_required(function):
    """Decorator para views baseadas em função."""

    def wrap(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_funcionario:
            raise PermissionDenied
        return function(request, *args, **kwargs)

    return wrap


class FuncionarioRequiredMixin(UserPassesTestMixin):
    """Mixin para views baseadas em classe."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_funcionario


class HospedeRequiredMixin(UserPassesTestMixin):
    """Mixin para views baseadas em classe para hóspedes."""

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_hospede
