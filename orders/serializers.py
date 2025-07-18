# orders/serializers.py
from rest_framework import serializers
from .models import Venda, ItemVenda

# Este serializer valida os dados que o frontend envia do carrinho
class CarrinhoItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1)

    class Meta:
        fields = ['product_id', 'quantity']

# Este serializer formata os itens da venda para a resposta da API
class ItemVendaOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemVenda
        fields = ['nome_produto', 'quantidade', 'preco_unitario', 'subtotal']

# Este serializer formata a venda completa para a resposta da API
class VendaOutputSerializer(serializers.ModelSerializer):
    itens = ItemVendaOutputSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    cliente_nome = serializers.CharField(source='cliente.first_name', read_only=True, default='Venda no Balcão')

    class Meta:
        model = Venda
        fields = ['id', 'status', 'status_display', 'payment_method', 'data_venda', 'valor_total', 'itens', 'cliente_nome']

class VendaStatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para permitir a atualização apenas do campo 'status' de uma Venda.
    """
    class Meta:
        model = Venda
        fields = ['status'] # Apenas este campo será aceito na requisição

