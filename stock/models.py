# stock/models.py
from django.db import models
from django.utils import timezone

# 1. NOVO MODELO PARA GERENCIAR FORNECEDORES
class Supplier(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Fornecedor")
    cnpj_cpf = models.CharField(max_length=18, unique=True, blank=True, null=True, verbose_name="CNPJ/CPF")
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name="Pessoa de Contato")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefone")
    email = models.EmailField(max_length=254, blank=True, null=True, verbose_name="Email")
    street = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rua")
    number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    neighborhood = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fornecedor"
        verbose_name_plural = "Fornecedores"
        ordering = ['name']


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nome da Categoria")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ['name']


class StockItem(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Item")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Categoria")
    
    # 2. CAMPO 'supplier' ALTERADO PARA UMA RELAÇÃO (ForeignKey)
    # Agora ele se conecta ao modelo Supplier acima.
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Fornecedor")

    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Quantidade")
    unit_of_measure = models.CharField(max_length=20, default="unidades", verbose_name="Unidade de Medida")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Preço de Custo")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Última Atualização")
    minimum_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Estoque Mínimo")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Data de Validade")
    image = models.ImageField(upload_to='stock_images/', null=True, blank=True, verbose_name="Foto do Item")

    profit_percentage = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=100.00, # Define um lucro padrão de 100% (dobro do custo)
        verbose_name="Margem de Lucro (%)",
        help_text="Percentual de lucro a ser aplicado sobre o preço de custo para sugerir o preço de venda."
    )

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit_of_measure})"
        
    @property
    def is_below_minimum_stock(self):
        return self.quantity < self.minimum_stock_level

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    def days_until_expiry(self):
        if not self.expiry_date:
            return None
        today = timezone.now().date()
        delta = self.expiry_date - today
        return delta.days

    class Meta:
        verbose_name = "Item de Estoque"
        verbose_name_plural = "Itens de Estoque"
        ordering = ['name']

# --- NOVO MODELO PARA PRODUTOS DO CARDÁPIO ---
class MenuProduct(models.Model):
    stock_item = models.ForeignKey(
        StockItem, 
        on_delete=models.CASCADE, # Se o item de estoque for deletado, o produto do cardápio também será.
        verbose_name="Item de Estoque de Origem",
        help_text="Selecione o item do estoque que será a base para este produto do cardápio."
    )
    name = models.CharField(
        max_length=100, 
        verbose_name="Nome no Cardápio",
        help_text="Nome que aparecerá para o cliente. Pode ser diferente do nome no estoque."
    )
    description = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Descrição do Produto",
        help_text="Uma breve descrição do produto para o cardápio."
    )
    sale_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Preço de Venda"
    )
    image = models.ImageField(
        upload_to='menu_product_images/', 
        blank=True, 
        null=True, 
        verbose_name="Foto no Cardápio",
        help_text="Foto específica para o cardápio. Se deixado em branco, pode-se usar a foto do item de estoque."
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Ativo no Cardápio?",
        help_text="Marque se este produto deve aparecer no cardápio para os clientes."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (R$ {self.sale_price})"

    class Meta:
        verbose_name = "Produto do Cardápio"
        verbose_name_plural = "Produtos do Cardápio"
        ordering = ['name']