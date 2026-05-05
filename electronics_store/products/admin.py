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


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'short_text', 'is_approved', 'created_at')
    list_editable = ('is_approved',)
    list_filter = ('is_approved', 'created_at', 'product')
    search_fields = ('product__name', 'user__username', 'user__email', 'text')
    readonly_fields = ('product', 'user', 'text', 'created_at')
    ordering = ('is_approved', '-created_at')
    actions = ('approve_reviews', 'unapprove_reviews')
    list_per_page = 30

    @admin.display(description='Текст отзыва')
    def short_text(self, obj):
        if len(obj.text) <= 80:
            return obj.text
        return f'{obj.text[:80]}...'

    @admin.action(description='Одобрить выбранные отзывы')
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'Одобрено отзывов: {updated}.')

    @admin.action(description='Снять одобрение с выбранных отзывов')
    def unapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'Снято одобрение с отзывов: {updated}.')


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'user', 'stars', 'created_at')
    list_filter = ('stars', 'created_at', 'product')
    search_fields = ('product__name', 'user__username', 'user__email')
    readonly_fields = ('product', 'user', 'stars', 'created_at')
    ordering = ('-created_at',)
    list_per_page = 30


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
