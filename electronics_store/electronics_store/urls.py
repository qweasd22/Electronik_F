from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),  # если есть приложение accounts
    path('products/', include('products.urls', namespace='products')),  # наш каталог
    path('orders/', include('orders.urls', namespace='orders')),
    path('', views.index, name='home'),
    path('blog/', include('blog.urls', namespace='blog')),
    
    
]

# Для медиа-файлов (картинки товаров)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Для статических файлов (css, javascript)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)