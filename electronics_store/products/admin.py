from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, Review, Rating

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# Inline для нескольких изображений
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('id',)

# Inline для отзывов
class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'text', 'is_approved', 'created_at')

# Inline для рейтингов
class RatingInline(admin.TabularInline):
    model = Rating
    extra = 1
    readonly_fields = ('user', 'stars', 'created_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'average_rating')
    list_filter = ('category', 'brand', 'sales')
    search_fields = ('name', 'description', 'additional_info')
    filter_horizontal = ('sales',)
    inlines = [ProductImageInline, ReviewInline, RatingInline]  # подключаем все inline

    # Добавляем отображение количества скидок
    def get_sales_count(self, obj):
        return obj.sales.count()
    get_sales_count.short_description = "Количество скидок"

    # Разделяем поля на группы для удобства
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'brand', 'price', 'stock', 'description', 'additional_info', 'image')
        }),
        ('Скидки', {
            'fields': ('sales',),
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
