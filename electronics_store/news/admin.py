from django.contrib import admin
from .models import News, Category

class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'published_at', 'category', 'is_published']
    list_filter = ['is_published', 'category']
    search_fields = ['title', 'summary']
    ordering = ['-published_at']
    

admin.site.register(News, NewsAdmin)
admin.site.register(Category)
