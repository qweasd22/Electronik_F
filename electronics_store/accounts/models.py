from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Добавим дополнительные поля, если нужно
    birth_date = models.DateField(null=True, blank=True,verbose_name='Дата рождения')
    phone_number = models.CharField(max_length=11, null=True, blank=True, verbose_name='Номер телефона')
    address = models.TextField(blank=True, null=True, verbose_name='Адрес')
    def __str__(self):
        return self.username
