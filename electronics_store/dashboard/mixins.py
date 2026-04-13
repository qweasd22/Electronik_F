from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class DashboardAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'account_login'  # если используешь allauth
    # login_url = 'login'  # если у тебя свой login url

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (
            user.is_superuser or
            user.is_staff
        )

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            raise PermissionDenied("У вас нет доступа к панели управления.")
        return super().handle_no_permission()