from django.shortcuts import get_object_or_404, render

from .models import Category, News


def news_list(request):
    """?????????? ?????? ???????? ? ???????????? ?????????? ?? ?????????."""
    category_filter = request.GET.get('category')
    news_qs = News.objects.filter(is_published=True)

    if category_filter:
        news_qs = news_qs.filter(category__name=category_filter)

    news = news_qs.order_by('-published_at')
    categories = Category.objects.all()

    return render(request, 'news/news_list.html', {
        'news': news,
        'categories': categories,
        'selected_category': category_filter,
    })


def news_detail(request, pk):
    """?????????? ????????? ???????."""
    news_item = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'news/news_detail.html', {'news': news_item})
