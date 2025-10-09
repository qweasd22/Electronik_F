from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'birth_date', 'phone_number')  # Укажем нужные поля

    # Добавим кастомные валидаторы или логику в случае необходимости