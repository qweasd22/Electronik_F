from django.urls import path

from .views import (
    CourierDashboardHomeView,
    CourierOrderDetailView,
    CourierOrderListView,
    CourierOrderStatusUpdateView,
)

app_name = 'courier_dashboard'

urlpatterns = [
    path('', CourierDashboardHomeView.as_view(), name='home'),
    path('orders/', CourierOrderListView.as_view(), name='order_list'),
    path('orders/<int:order_id>/', CourierOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:order_id>/status/', CourierOrderStatusUpdateView.as_view(), name='order_status_update'),
]
