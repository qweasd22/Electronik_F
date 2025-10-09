from django.contrib import admin
from .models import Category, Brand, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name',)

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'brand', 'price', 'stock', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('category', 'brand')
    search_fields = ('name', 'description')

from django.contrib import admin
from .models import Category, Brand, Product, Review, Rating

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    actions = ['approve_reviews', 'reject_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Одобрить выбранные отзывы"

    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    reject_reviews.short_description = "Отклонить выбранные отзывы"

class RatingAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'stars', 'created_at')
    list_filter = ('stars', 'created_at')




admin.site.register(Review, ReviewAdmin)
admin.site.register(Rating, RatingAdmin)
