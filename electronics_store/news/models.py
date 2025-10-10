from django.db import models
from django.utils import timezone

class Category(models.Model):
    """Категории новостей"""
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class News(models.Model):
    """Модель новостных постов"""
    title = models.CharField("Заголовок", max_length=255)
    summary = models.TextField("Краткое описание", max_length=500)
    content = models.TextField("Полное содержание")
    published_at = models.DateTimeField("Дата публикации", default=timezone.now)
    category = models.ForeignKey(Category, related_name="news", on_delete=models.SET_NULL, null=True, blank=True)
    image = models.ImageField(upload_to='news/', blank=True, null=True)  # Изображение
    is_published = models.BooleanField("Опубликовано", default=True)

    class Meta:
        ordering = ['-published_at']  # Новости выводятся по убыванию даты
        verbose_name = "Новость"
        verbose_name_plural = "Новости"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/news/{self.id}/"  # Страница подробного просмотра новости
