# stock/serializers.py
from rest_framework import serializers
from .models import StockItem, Category, Supplier, MenuProduct

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class StockItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, allow_null=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_below_minimum_stock = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True, allow_null=True)
    suggested_sale_price = serializers.SerializerMethodField()

    class Meta:
        model = StockItem
        fields = [
            'id', 'name', 'category', 'category_name', 
            'supplier', 'supplier_name',
            'quantity', 'unit_of_measure', 'cost_price', 'profit_percentage', 'last_updated', 
            'minimum_stock_level', 'image', 'expiry_date',
            'is_expired',
            'is_below_minimum_stock',
            'days_until_expiry', 'suggested_sale_price'
        ]
        read_only_fields = [
            'last_updated', 'category_name', 'supplier_name',
            'is_expired', 'is_below_minimum_stock', 'days_until_expiry', 'suggested_sale_price'
        ]

    def get_suggested_sale_price(self, obj):
        # Verifica se o item tem os campos necessários para o cálculo
        if obj.cost_price and hasattr(obj, 'profit_percentage') and obj.profit_percentage is not None:
            # Converte a porcentagem para um fator de multiplicação
            markup = 1 + (obj.profit_percentage / 100)
            # Calcula o preço
            suggested_price = obj.cost_price * markup
            # Retorna o valor arredondado para 2 casas decimais
            return round(suggested_price, 2)
        # Se não for possível calcular, retorna None
        return None

# --- SERIALIZER CORRIGIDO PARA O MODELO MENUPRODUCT ---
class MenuProductSerializer(serializers.ModelSerializer):
    # Campos de leitura para dados relacionados
    stock_item_name = serializers.CharField(source='stock_item.name', read_only=True, allow_null=True)
    stock_item_category_name = serializers.CharField(source='stock_item.category.name', read_only=True, allow_null=True)
    stock_item_quantity = serializers.DecimalField(source='stock_item.quantity', max_digits=10, decimal_places=2, read_only=True)
    cost_price = serializers.DecimalField(source='stock_item.cost_price', max_digits=10, decimal_places=2, read_only=True, allow_null=True) # <-- NOVO
    supplier_name = serializers.CharField(source='stock_item.supplier.name', read_only=True, allow_null=True) # <-- NOVO

    # Campos de imagem
    image_url = serializers.ImageField(source='image', read_only=True, use_url=True)
    stock_item_image_url = serializers.ImageField(source='stock_item.image', read_only=True, use_url=True)

    class Meta:
        model = MenuProduct
        fields = [
            'id', 
            'stock_item', 
            'stock_item_name',
            'stock_item_category_name', 
            'stock_item_quantity',
            'name', 
            'description', 
            'sale_price',
            'cost_price', # <-- NOVO
            'supplier_name', # <-- NOVO
            'image',
            'image_url',
            'stock_item_image_url',
            'is_active',
            'created_at', 
            'updated_at'
        ]
        read_only_fields = (
            'stock_item_name', 
            'stock_item_category_name',
            'stock_item_quantity',
            'cost_price', # <-- NOVO
            'supplier_name', # <-- NOVO
            'image_url',
            'stock_item_image_url',
            'created_at', 
            'updated_at'
        )
        extra_kwargs = {
            'stock_item': {'write_only': True, 'required': True},
            'image': {'write_only': True, 'required': False},
        }