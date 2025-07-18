from rest_framework import generics, permissions
from users.views import IsEquipe # Importa sua permissão IsEquipe

from .models import StockItem, Category, Supplier, MenuProduct
from .serializers import StockItemSerializer, CategorySerializer, SupplierSerializer, MenuProductSerializer

# --- Views para Fornecedores (Supplier) ---
class SupplierListCreateView(generics.ListCreateAPIView):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]

class SupplierRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView): # <-- CORRIGIDO
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]
    lookup_field = 'pk'

# --- Views para Categorias (Category) ---
class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]

class CategoryRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView): # <-- CORRIGIDO
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]
    lookup_field = 'pk'

# --- Views para Itens de Estoque (StockItem) ---
class StockItemListCreateView(generics.ListCreateAPIView):
    queryset = StockItem.objects.select_related('category', 'supplier').all()
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]

class StockItemRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView): # <-- CORRIGIDO
    queryset = StockItem.objects.select_related('category', 'supplier').all()
    serializer_class = StockItemSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]
    lookup_field = 'pk'

# --- Views para Produtos do Cardápio (MenuProduct) ---
class MenuProductListCreateView(generics.ListCreateAPIView):
    serializer_class = MenuProductSerializer

    def get_queryset(self):
        """
        Retorna todos os produtos para a equipe de gerenciamento
        e apenas os produtos ativos para visualização pública.
        """
        user = self.request.user
        
        # Verifica se o usuário é autenticado e pertence à equipe
        if user.is_authenticated and IsEquipe().has_permission(self.request, self):
            # Se for da equipe, retorna TODOS os produtos
            return MenuProduct.objects.select_related('stock_item').all()
        
        # Para todos os outros (público), retorna apenas os produtos ativos
        return MenuProduct.objects.select_related('stock_item').filter(is_active=True)

    def get_permissions(self):
        """
        Define as permissões com base no método da requisição.
        GET (ver a lista) é público.
        POST (criar um item) é restrito à equipe.
        """
        if self.request.method == 'GET':
            # Permite que qualquer um veja o cardápio (a lógica do get_queryset vai filtrar)
            return [permissions.AllowAny()] 
        # Apenas a equipe pode criar produtos
        return [permissions.IsAuthenticated(), IsEquipe()]

class MenuProductRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView): # <-- CORRIGIDO
    queryset = MenuProduct.objects.all()
    serializer_class = MenuProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]
    lookup_field = 'pk'

class MenuProductReportView(generics.ListAPIView):
    """
    View para fornecer uma lista completa de todos os produtos do cardápio
    com dados detalhados do estoque para relatórios internos.
    Otimizado para reduzir o número de queries no banco de dados.
    """
    serializer_class = MenuProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe] # Apenas a equipe pode ver

    def get_queryset(self):
        # Usamos select_related para otimizar a busca, trazendo os dados
        # de StockItem, Category e Supplier em uma única query.
        return MenuProduct.objects.select_related(
            'stock_item', 
            'stock_item__category', 
            'stock_item__supplier'
        ).all().order_by('name')