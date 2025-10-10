# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CustomUserChangeForm
from orders.models import Order

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('accounts:profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile(request):
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('accounts:profile')
    else:
        form = CustomUserChangeForm(instance=request.user)

    # Получаем все заказы текущего пользователя
    orders = Order.objects.filter(user=request.user)

    return render(request, 'accounts/profile.html', {'form': form, 'orders': orders})

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
@login_required
def cancel_order(request, order_id):
    """Отмена заказа пользователем"""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status == 'delivered':
        messages.error(request, f"Заказ {order.id} уже доставлен и не может быть отменен.")
    else:
        try:
            order.cancel()  # Попытка отмены
            messages.success(request, f"Заказ {order.id} успешно отменен.")
        except ValueError as e:
            messages.error(request, str(e))  # Показ ошибки, если заказ уже доставлен

    return redirect('accounts:profile')  # Перенаправляем на страницу профиля