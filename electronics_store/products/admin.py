from django.contrib import admin
from .models import Category, Brand, Product, ProductImage, Review, Rating, Promotion, Discount

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('id',)

class ReviewInline(admin.TabularInline):
    model = Review
    extra = 1
    readonly_fields = ('user', 'created_at')
    fields = ('user', 'text', 'is_approved', 'created_at')

class RatingInline(admin.TabularInline):
    model = Rating
    extra = 1
    readonly_fields = ('user', 'stars', 'created_at')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'average_rating')
    list_filter = ('category', 'brand',)
    search_fields = ('name', 'description')
    inlines = [ProductImageInline, ReviewInline, RatingInline]

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'text', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('text', 'user__username', 'product__name')
    actions = ['approve_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, "Выбранные отзывы одобрены.")
    approve_reviews.short_description = "Одобрить выбранные отзывы"

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'stars', 'created_at')
    list_filter = ('stars', 'created_at')
    search_fields = ('user__username', 'product__name')

from django.contrib import admin


class DiscountAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount_percent', 'start_date', 'end_date', 'active')
    list_filter = ('active', 'start_date', 'end_date')
    search_fields = ('name',)

# Модель для акций
class PromotionAdmin(admin.ModelAdmin):
    list_display = ('name', 'discount', 'start_date', 'end_date', 'active')
    list_filter = ('active', 'start_date', 'end_date')
    search_fields = ('name',)

admin.site.register(Discount, DiscountAdmin)
admin.site.register(Promotion, PromotionAdmin)