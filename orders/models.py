# orders/models.py
from django.db import models
from django.conf import settings

class Venda(models.Model):
    STATUS_CHOICES = [
        ('AGUARDANDO_PAGAMENTO', 'Aguardando Pagamento'),
        ('PAGO', 'Pago'),
        ('EM_PREPARO', 'Em Preparo'),
        ('PRONTO', 'Pronto para Retirada'),
        ('FINALIZADO', 'Finalizado/Entregue'),
        ('CANCELADO', 'Cancelado'),
    ]

    # --- OPÇÕES DE PAGAMENTO ATUALIZADAS ---
    PAYMENT_CHOICES = [
        ('NA_RETIRADA', 'Pagar na Retirada'), # Usado pelo cardápio online
        ('ONLINE', 'Pago Online'),             # Usado pelo cardápio online
        ('DINHEIRO', 'Dinheiro'),              # Usado pelo PDV
        ('CARTAO_DEBITO', 'Cartão de Débito'), # Usado pelo PDV
        ('CARTAO_CREDITO', 'Cartão de Crédito'),# Usado pelo PDV
        ('PIX', 'Pix'),                        # Usado pelo PDV
    ]

    id = models.AutoField(primary_key=True)
    cliente = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES, 
        default='PAGO', # Vendas de balcão já entram como pagas
        verbose_name="Status"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default='DINHEIRO', # Um padrão para o PDV
        verbose_name="Método de Pagamento"
    )
    data_venda = models.DateTimeField(auto_now_add=True, verbose_name="Data da Venda")
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Valor Total")
    
    def __str__(self):
        return f"Venda #{self.id} ({self.get_status_display()}) - R$ {self.valor_total}"

    class Meta:
        verbose_name = "Venda"
        verbose_name_plural = "Vendas"
        ordering = ['-data_venda']


class ItemVenda(models.Model):
    id = models.AutoField(primary_key=True)
    venda = models.ForeignKey(Venda, related_name='itens', on_delete=models.CASCADE, verbose_name="Venda")
    produto = models.ForeignKey(
        'stock.MenuProduct', 
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Produto do Cardápio"
    )
    nome_produto = models.CharField(max_length=255, verbose_name="Nome do Produto na Venda")
    quantidade = models.PositiveIntegerField(verbose_name="Quantidade")
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço Unitário na Venda")
    
    # Removido o campo subtotal para ser uma property, é mais seguro
    @property
    def subtotal(self):
        return self.preco_unitario * self.quantidade

    def __str__(self):
        return f"{self.quantidade}x {self.nome_produto} (Venda #{self.venda.id})"

    class Meta:
        verbose_name = "Item de Venda"
        verbose_name_plural = "Itens de Venda"