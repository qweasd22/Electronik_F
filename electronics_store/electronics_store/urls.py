from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # Для регистрации и аутентификации
    
    # path('products/', include('products.urls')),  # Для каталога товаров
    # path('orders/', include('orders.urls')),  # Для корзины и заказов
    # path('blog/', include('blog.urls')),  # Для блога
    # path('promotions/', include('promotions.urls')),  # Для акций и скидок
]
