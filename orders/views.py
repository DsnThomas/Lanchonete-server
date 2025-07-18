# orders/views.py
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate
from rest_framework import status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.views import IsEquipe
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

# Modelos dos apps
from .models import Venda, ItemVenda
from stock.models import MenuProduct, StockItem # <-- Importamos o StockItem

# Serializers
from .serializers import CarrinhoItemInputSerializer, VendaOutputSerializer, VendaStatusUpdateSerializer

class CriarVendaView(APIView):
    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        carrinho_data = request.data.get('items', [])
        payment_method = request.data.get('payment_method')

        # Validação para garantir que o método de pagamento foi enviado
        if not payment_method:
            return Response({"error": "Método de pagamento é obrigatório."}, status=status.HTTP_400_BAD_REQUEST)

        carrinho_serializer = CarrinhoItemInputSerializer(data=carrinho_data, many=True)
        if not carrinho_serializer.is_valid():
            return Response(carrinho_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        carrinho_validado = carrinho_serializer.validated_data
        valor_total_pedido = 0
        itens_para_processar = []

        for item_data in carrinho_validado:
            try:
                produto = MenuProduct.objects.select_related('stock_item').get(id=item_data['product_id'])
                if produto.stock_item.quantity < item_data['quantity']:
                    return Response(
                        {"error": f"Estoque insuficiente para: {produto.name}. Disponível: {produto.stock_item.quantity}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                stock_item_associado = produto.stock_item
                stock_item_associado.quantity -= item_data['quantity']
                stock_item_associado.save()

                subtotal = produto.sale_price * item_data['quantity']
                valor_total_pedido += subtotal
                itens_para_processar.append({
                    "produto": produto, "nome_produto": produto.name,
                    "quantidade": item_data['quantity'], "preco_unitario": produto.sale_price,
                    "subtotal": subtotal
                })
            except MenuProduct.DoesNotExist:
                return Response({"error": f"Produto com ID {item_data['product_id']} não encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # --- LÓGICA DE STATUS CORRIGIDA ---
        # Define o status inicial baseado na origem da venda
        
        # Vendas de balcão (PDV) já são consideradas pagas.
        # Vendas do cardápio online ficam aguardando a confirmação.
        vendas_pdv = ['DINHEIRO', 'CARTAO_DEBITO', 'CARTAO_CREDITO', 'PIX']
        if payment_method in vendas_pdv:
            initial_status = 'PAGO'
        else: # Para 'NA_RETIRADA' e 'ONLINE' do cardápio do cliente
            initial_status = 'AGUARDANDO_PAGAMENTO'

        # Atribui o cliente apenas se ele estiver logado e NÃO for uma venda anônima de PDV
        cliente_final = None
        if request.user.is_authenticated and payment_method in ['ONLINE', 'NA_RETIRADA']:
            cliente_final = request.user
        
        nova_venda = Venda.objects.create(
            cliente=cliente_final,
            valor_total=valor_total_pedido,
            status=initial_status, # <-- Status dinâmico
            payment_method=payment_method
        )
        
        for item_info in itens_para_processar:
            ItemVenda.objects.create(
                venda=nova_venda, produto=item_info['produto'], nome_produto=item_info['nome_produto'],
                quantidade=item_info['quantidade'], preco_unitario=item_info['preco_unitario']
            )

        venda_criada_serializer = VendaOutputSerializer(nova_venda)
        return Response(venda_criada_serializer.data, status=status.HTTP_201_CREATED)


class PedidoAtivoListView(generics.ListAPIView):
    """
    View para listar todos os pedidos que não estão Finalizados ou Cancelados.
    """
    serializer_class = VendaOutputSerializer
    permission_classes = [permissions.IsAuthenticated, IsEquipe]

    def get_queryset(self):
        return Venda.objects.exclude(status__in=['FINALIZADO', 'CANCELADO']).order_by('data_venda')


# --- CLASSE ALTERADA COM A CORREÇÃO DO BUG ---
class VendaDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View para ver detalhes, atualizar o status (com lógica de estorno) ou deletar uma venda.
    """
    queryset = Venda.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsEquipe]
    lookup_field = 'pk'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VendaStatusUpdateSerializer
        return VendaOutputSerializer

    def update(self, request, *args, **kwargs):
        # Usamos uma transação atômica para garantir a integridade dos dados.
        # Ou tudo funciona, ou nada é salvo no banco.
        with transaction.atomic():
            venda = self.get_object()
            status_antigo = venda.status
            status_novo = request.data.get('status')

            # LÓGICA DE ESTORNO DE ESTOQUE
            # Só executa se o status anterior NÃO era 'CANCELADO' e o novo status É 'CANCELADO'
            if status_novo == 'CANCELADO' and status_antigo != 'CANCELADO':
                # Itera sobre cada item que foi vendido neste pedido
                for item_vendido in venda.itens.all():
                    # Verifica se o produto ainda existe
                    if item_vendido.produto and item_vendido.produto.stock_item:
                        stock_item = item_vendido.produto.stock_item
                        # Devolve a quantidade ao estoque de forma segura
                        stock_item.quantity += item_vendido.quantidade
                        stock_item.save()

            # Chama o método 'update' original para salvar a mudança de status
            return super().update(request, *args, **kwargs)


class UserOrderListView(generics.ListAPIView):
    """
    View para listar todos os pedidos de um usuário autenticado.
    """
    serializer_class = VendaOutputSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filtra as vendas para retornar apenas as do usuário que fez a requisição.
        """
        user = self.request.user
        return Venda.objects.filter(cliente=user).order_by('-data_venda')


class ConfirmarPagamentoView(APIView):
    """
    View dedicada para um cliente confirmar que o pagamento online foi realizado.
    """
    permission_classes = [IsAuthenticated] # Apenas usuários logados

    def post(self, request, pk):
        try:
            # Encontra a venda pelo ID (pk) fornecido na URL
            venda = Venda.objects.get(pk=pk)

            # --- VERIFICAÇÃO DE SEGURANÇA ---
            # Garante que o usuário logado é o dono do pedido
            if venda.cliente != request.user:
                return Response(
                    {"error": "Você não tem permissão para modificar este pedido."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Garante que o status só possa ser alterado se estiver aguardando
            if venda.status != 'AGUARDANDO_PAGAMENTO':
                 return Response(
                    {"error": f"Este pedido não pode ser pago, status atual: {venda.get_status_display()}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Se tudo estiver certo, atualiza o status para PAGO
            venda.status = 'PAGO'
            venda.save()

            # Retorna os dados do pedido atualizado
            serializer = VendaOutputSerializer(venda)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Venda.DoesNotExist:
            return Response({"error": "Pedido não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        
class RelatorioVendasView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEquipe]

    def get(self, request):
        # Pega as datas da query string, com um padrão de 30 dias atrás
        end_date = timezone.now().date()
        start_date = request.query_params.get('start_date', end_date - timezone.timedelta(days=30))
        
        # Filtra as vendas no período desejado e que não foram canceladas
        vendas_no_periodo = Venda.objects.filter(
            data_venda__date__range=[start_date, end_date],
            status__in=['PAGO', 'EM_PREPARO', 'PRONTO', 'FINALIZADO']
        )

        # 1. Resumo Geral
        resumo = vendas_no_periodo.aggregate(
            faturamento_total=Sum('valor_total'),
            total_pedidos=Count('id'),
            ticket_medio=Avg('valor_total')
        )

        # 2. Vendas ao Longo do Tempo (para o gráfico)
        vendas_por_dia = vendas_no_periodo.annotate(
            dia=TruncDate('data_venda')
        ).values('dia').annotate(
            total=Sum('valor_total')
        ).order_by('dia')

        # 3. Produtos mais vendidos
        produtos_vendidos = ItemVenda.objects.filter(
            venda__in=vendas_no_periodo
        ).values('nome_produto').annotate(
            quantidade_vendida=Sum('quantidade')
        ).order_by('-quantidade_vendida')[:10] # Top 10

        # 4. Vendas por método de pagamento
        vendas_por_pagamento = vendas_no_periodo.values(
            'payment_method'
        ).annotate(
            total=Sum('valor_total')
        ).order_by('-total')


        # Monta a resposta final da API
        data = {
            'resumo': {
                'faturamento_total': resumo['faturamento_total'] or 0,
                'total_pedidos': resumo['total_pedidos'] or 0,
                'ticket_medio': resumo['ticket_medio'] or 0,
            },
            'vendas_por_dia': list(vendas_por_dia),
            'top_produtos': list(produtos_vendidos),
            'vendas_por_pagamento': list(vendas_por_pagamento),
        }
        
        return Response(data)
    

class ProductProfitabilityView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEquipe]

    def get(self, request):
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        # Começamos com todos os itens de vendas de pedidos concluídos
        items_vendidos = ItemVenda.objects.filter(
            venda__status__in=['PAGO', 'FINALIZADO']
        )

        # Filtra por data se os parâmetros forem fornecidos
        if start_date_str and end_date_str:
            items_vendidos = items_vendidos.filter(venda__data_venda__date__range=[start_date_str, end_date_str])

        # Agrupa por produto e calcula os totais usando o poder do banco de dados
        lucratividade = items_vendidos.values(
            'produto__name' # Agrupa pelo nome do produto do cardápio
        ).annotate(
            quantidade_total=Sum('quantidade'),
            receita_total=Sum(F('quantidade') * F('preco_unitario')),
            # Pega o preço de custo do item de estoque associado
            custo_total=Sum(F('quantidade') * F('produto__stock_item__cost_price'))
        ).order_by('-receita_total')

        # Calcula o lucro e a margem em Python para cada item agrupado
        report_data = []
        for item in lucratividade:
            # Garante que não haverá erro se um dos valores for None
            receita = item['receita_total'] or 0
            custo = item['custo_total'] or 0
            
            lucro_bruto = receita - custo
            margem = (lucro_bruto / receita * 100) if receita > 0 else 0
            
            report_data.append({
                'nome_produto': item['produto__name'],
                'quantidade_vendida': item['quantidade_total'],
                'receita_total': receita,
                'custo_total': custo,
                'lucro_bruto': lucro_bruto,
                'margem_lucro_percentual': round(margem, 2)
            })

        return Response(report_data)