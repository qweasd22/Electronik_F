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
]