from django.urls import path
from . import views
from .views import product_detail

app_name = 'products'

urlpatterns = [
    path('', views.product_list, name='product_list'),  # Каталог товаров
    path('<int:id>/', views.product_detail, name='product_detail'),  # Детали товара
]
