from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, Review, Rating


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('id',)


class ReviewInline(admin.TabularInline):
    model = Review
    extra = 0
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'text', 'is_approved', 'created_at')


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('user', 'stars', 'created_at')
    fields = ('user', 'stars', 'created_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'category',
        'brand',
        'price',
        'stock',
        'average_rating',
        'get_sales_count',
        'created_at',
    )
    list_filter = ('category', 'brand', 'sales', 'created_at')
    search_fields = ('name', 'description', 'additional_info')
    ordering = ('-created_at',)
    list_per_page = 20

    filter_horizontal = ('sales',)
    inlines = [ProductImageInline, ReviewInline, RatingInline]

    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'name',
                'slug',
                'category',
                'brand',
                'price',
                'stock',
                'image',
            )
        }),
        ('Описание товара', {
            'fields': (
                'description',
                'additional_info',
            )
        }),
        ('Скидки', {
            'fields': ('sales',)
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    @admin.display(description='Количество скидок')
    def get_sales_count(self, obj):
        return obj.sales.count()