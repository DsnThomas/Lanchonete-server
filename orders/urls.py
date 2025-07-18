# orders/urls.py
from django.urls import path
from .views import CriarVendaView, PedidoAtivoListView, VendaDetailView, UserOrderListView, ConfirmarPagamentoView
from .views import RelatorioVendasView, ProductProfitabilityView

urlpatterns = [
    path('sales/create/', CriarVendaView.as_view(), name='create-sale'),
    path('sales/active/', PedidoAtivoListView.as_view(), name='active-sales-list'),
    path('sales/<int:pk>/', VendaDetailView.as_view(), name='sale-detail'),
    path('sales/<int:pk>/confirm-payment/', ConfirmarPagamentoView.as_view(), name='confirm-payment'),
    path('my-orders/', UserOrderListView.as_view(), name='my-orders'),
    path('reports/sales/', RelatorioVendasView.as_view(), name='sales-report'),
    path('reports/sales/', RelatorioVendasView.as_view(), name='sales-report'),
    path('reports/product-profitability/', ProductProfitabilityView.as_view(), name='product-profitability-report'),
]