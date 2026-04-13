from django.contrib import admin
from .models import News, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'published_at', 'is_published')
    list_filter = ('is_published', 'category', 'published_at')
    search_fields = ('title', 'summary')
    ordering = ('-published_at',)
    list_editable = ('is_published',)
    list_per_page = 20
    date_hierarchy = 'published_at'