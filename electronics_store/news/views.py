from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from .models import News, Category

def news_list(request):
    """Отображает список новостей с возможностью фильтрации по категории"""
    category_filter = request.GET.get('category')
    if category_filter:
        news = News.objects.filter(is_published=True, category__name=category_filter)
    else:
        news = News.objects.filter(is_published=True)
    
    categories = Category.objects.all()  # Для фильтрации
    return render(request, 'news/news_list.html', {
        'news': news,
        'categories': categories,
        'selected_category': category_filter
    })

def news_detail(request, pk):
    """Отображает подробную новость"""
    news_item = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'news/news_detail.html', {'news': news_item})
