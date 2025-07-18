# stock/urls.py
from django.urls import path
from .views import (
    StockItemListCreateView,
    StockItemRetrieveUpdateDestroyView,
    CategoryListCreateView,
    CategoryRetrieveUpdateDestroyView,
    SupplierListCreateView,
    SupplierRetrieveUpdateDestroyView,
    # 1. IMPORTAMOS AS NOVAS VIEWS DE MenuProduct
    MenuProductListCreateView,
    MenuProductRetrieveUpdateDestroyView,
    MenuProductReportView
)

urlpatterns = [
    # URLs para Fornecedores
    path('suppliers/', SupplierListCreateView.as_view(), name='supplier-list-create'),
    path('suppliers/<int:pk>/', SupplierRetrieveUpdateDestroyView.as_view(), name='supplier-detail'),
    
    # URLs para Categorias
    path('categories/', CategoryListCreateView.as_view(), name='category-list-create'),
    path('categories/<int:pk>/', CategoryRetrieveUpdateDestroyView.as_view(), name='category-detail'),
    
    # URLs para Itens de Estoque
    path('items/', StockItemListCreateView.as_view(), name='stockitem-list-create'),
    path('items/<int:pk>/', StockItemRetrieveUpdateDestroyView.as_view(), name='stockitem-detail'),

    # URLs PARA PRODUTOS DO CARDÁPIO (MenuProduct)
    path('menu-products/', MenuProductListCreateView.as_view(), name='menuproduct-list-create'),
    path('menu-products/<int:pk>/', MenuProductRetrieveUpdateDestroyView.as_view(), name='menuproduct-detail'),
    path('reports/all-products/', MenuProductReportView.as_view(), name='report-all-products'),
]