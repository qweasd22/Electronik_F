from django.urls import path

from .views import (
    DashboardHomeView,
    DashboardOrderDetailView,
    DashboardOrderListView,
    DashboardOrderStatusUpdateView,
    DashboardProductCreateView,
    DashboardProductDeleteView,
    DashboardProductListView,
    DashboardProductUpdateView,
    DashboardUserDetailView,
    DashboardUserListView,
    DashboardUserUpdateView,
    DashboardNewsListView,
    DashboardNewsCreateView,
    DashboardNewsUpdateView,
    DashboardNewsDeleteView,
    DashboardNewsTogglePublishView,
    DashboardSaleListView,
    DashboardSaleCreateView,
    DashboardSaleUpdateView,
    DashboardSaleDeleteView,
    DashboardSaleToggleActiveView,
)

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardHomeView.as_view(), name='home'),

    path('orders/', DashboardOrderListView.as_view(), name='order_list'),
    path('orders/<int:order_id>/', DashboardOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:order_id>/status/', DashboardOrderStatusUpdateView.as_view(), name='order_status_update'),

    path('products/', DashboardProductListView.as_view(), name='product_list'),
    path('products/create/', DashboardProductCreateView.as_view(), name='product_create'),
    path('products/<int:product_id>/edit/', DashboardProductUpdateView.as_view(), name='product_update'),
    path('products/<int:product_id>/delete/', DashboardProductDeleteView.as_view(), name='product_delete'),

    path('users/', DashboardUserListView.as_view(), name='user_list'),
    path('users/<int:user_id>/', DashboardUserDetailView.as_view(), name='user_detail'),
    path('users/<int:user_id>/edit/', DashboardUserUpdateView.as_view(), name='user_update'),

    path('news/', DashboardNewsListView.as_view(), name='news_list'),
    path('news/create/', DashboardNewsCreateView.as_view(), name='news_create'),
    path('news/<int:news_id>/edit/', DashboardNewsUpdateView.as_view(), name='news_update'),
    path('news/<int:news_id>/delete/', DashboardNewsDeleteView.as_view(), name='news_delete'),
    path('news/<int:news_id>/toggle-publish/', DashboardNewsTogglePublishView.as_view(), name='news_toggle_publish'),

    path('sales/', DashboardSaleListView.as_view(), name='sale_list'),
    path('sales/create/', DashboardSaleCreateView.as_view(), name='sale_create'),
    path('sales/<int:sale_id>/edit/', DashboardSaleUpdateView.as_view(), name='sale_update'),
    path('sales/<int:sale_id>/delete/', DashboardSaleDeleteView.as_view(), name='sale_delete'),
    path('sales/<int:sale_id>/toggle-active/', DashboardSaleToggleActiveView.as_view(), name='sale_toggle_active'),
]