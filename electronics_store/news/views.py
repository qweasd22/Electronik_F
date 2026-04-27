from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from .models import Category, News


def news_list(request):
    """?????????? ?????? ???????? ? ???????????? ?????????? ?? ?????????."""
    category_filter = request.GET.get('category')
    news_qs = News.objects.filter(is_published=True)

    if category_filter:
        news_qs = news_qs.filter(category__name=category_filter)

    news = news_qs.order_by('-published_at')
    paginator = Paginator(news, 6)
    page_obj = paginator.get_page(request.GET.get("page", 1))
    news = list(page_obj.object_list)

    query_params = request.GET.copy()
    query_params.pop("page", None)
    pagination_query = query_params.urlencode()

    categories = Category.objects.all()

    return render(request, 'news/news_list.html', {
        'news': news,
        "page_obj": page_obj,
        'categories': categories,
        'selected_category': category_filter,
        "pagination_query": pagination_query,
    })


def news_detail(request, pk):
    """?????????? ????????? ???????."""
    news_item = get_object_or_404(News, pk=pk, is_published=True)
    return render(request, 'news/news_detail.html', {'news': news_item})
