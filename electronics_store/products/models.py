from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    screen_size = models.CharField(max_length=100, null=True, blank=True)
    processor = models.CharField(max_length=100, null=True, blank=True)
    memory = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.name
    def average_rating(self):
        reviews = self.reviews.filter(approved=True)
        if reviews.exists():
            return reviews.aggregate(models.Avg('rating'))['rating__avg']
        return None
class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    is_main = models.BooleanField(default=False)  # Для главного изображения

    def __str__(self):
        return f"{self.product.name} - {self.id}"
    
from accounts.models import CustomUser
from django.db import models

class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])  # Оценка от 1 до 5
    comment = models.TextField()
    approved = models.BooleanField(default=False)  # Для модерации

    def __str__(self):
        return f"Review for {self.product.name} by {self.user.username}"
