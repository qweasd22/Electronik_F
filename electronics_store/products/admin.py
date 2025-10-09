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
