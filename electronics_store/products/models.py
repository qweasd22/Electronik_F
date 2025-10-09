from django.db import models
from accounts.models import CustomUser

class Category(models.Model):
    name = models.CharField("Название категории", max_length=100, unique=True)
    slug = models.SlugField("Слаг", max_length=100, unique=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField("Бренд", max_length=100, unique=True)

    class Meta:
        verbose_name = "Бренд"
        verbose_name_plural = "Бренды"

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField("Название товара", max_length=200)
    slug = models.SlugField("Слаг", max_length=200, unique=True)
    category = models.ForeignKey(Category, verbose_name="Категория", on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, verbose_name="Бренд", on_delete=models.CASCADE, related_name='products')
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField("Количество на складе", default=0)
    image = models.ImageField("Изображение", upload_to='products/', blank=True, null=True)
    screen_size = models.CharField("Размер экрана", max_length=100, blank=True, null=True)
    processor = models.CharField("Процессор", max_length=100, blank=True, null=True)
    memory = models.CharField("Оперативная память", max_length=100, blank=True, null=True)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"

    def __str__(self):
        return self.name

    def average_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return round(sum([rating.stars for rating in ratings]) / len(ratings), 1)
        return 0

class ProductImage(models.Model):
    product = models.ForeignKey(Product, verbose_name="Товар", related_name='images', on_delete=models.CASCADE)
    image = models.ImageField("Изображение", upload_to='product_images/')
    is_main = models.BooleanField("Главное изображение", default=False)

    class Meta:
        verbose_name = "Фото товара"
        verbose_name_plural = "Фото товаров"

    def __str__(self):
        return f"{self.product.name} - {self.id}"

class Review(models.Model):
    product = models.ForeignKey(Product, verbose_name="Товар", related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE)
    text = models.TextField("Текст отзыва")
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    is_approved = models.BooleanField("Одобрен", default=False)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв от {self.user.username} на {self.product.name}"

class Rating(models.Model):
    product = models.ForeignKey(Product, verbose_name="Товар", related_name='ratings', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE)
    stars = models.IntegerField("Оценка", choices=[(i, f'{i} ⭐') for i in range(1, 6)])
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    class Meta:
        verbose_name = "Рейтинг"
        verbose_name_plural = "Рейтинги"

    def __str__(self):
        return f"{self.user.username} оценил {self.product.name} на {self.stars} ⭐"
