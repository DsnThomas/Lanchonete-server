# stock/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import StockItem, Category, Supplier, MenuProduct # 1. Importamos Supplier e MenuProduct

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# 2. ADMIN PARA SUPPLIER (FORNECEDOR) - Adicionado para completude
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'cnpj_cpf', 'contact_person', 'phone', 'email', 'city')
    search_fields = ('name', 'cnpj_cpf', 'contact_person', 'email', 'city', 'street')

@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = (
        'name', 
        'category',
        'supplier', # Adicionando o fornecedor na lista
        'quantity', 
        'vencido', 
        'estoque_baixo', 
        'dias_para_vencer', 
        'last_updated'
    )
    search_fields = ('name', 'unit_of_measure', 'category__name', 'supplier__name') # Busca por nome do fornecedor
    list_filter = ('category', 'supplier', 'unit_of_measure', 'expiry_date') # Filtro por fornecedor
    readonly_fields = ('last_updated',)
    fieldsets = (
        (None, {'fields': ('name', 'category', 'supplier', 'quantity', 'unit_of_measure')}), # Adicionado supplier ao form
        ('Detalhes de Custo e Controle', {'fields': ('cost_price', 'minimum_stock_level', 'expiry_date', 'image')}), # Movido image para cá
        ('Informações de Sistema', {'fields': ('last_updated',)}),
    )

    @admin.display(description='Vencido?', boolean=True, ordering='expiry_date')
    def vencido(self, obj):
        return obj.is_expired

    @admin.display(description='Estoque Baixo?', boolean=True)
    def estoque_baixo(self, obj):
        return obj.is_below_minimum_stock
    
    @admin.display(description='Dias para Vencer', ordering='expiry_date')
    def dias_para_vencer(self, obj):
        days = obj.days_until_expiry()
        if days is None:
            return "N/A"
        if days < 0:
            return format_html('<span style="color: red; font-weight: bold;">Venceu há {} dias</span>', abs(days))
        if days <= 7: # Alerta para itens vencendo em 7 dias ou menos
            return format_html('<span style="color: orange; font-weight: bold;">{}</span>', days)
        return days

# 3. NOVO ADMIN PARA MENUPRODUCT (PRODUTO DO CARDÁPIO)
@admin.register(MenuProduct)
class MenuProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock_item_link', 'sale_price', 'is_active', 'updated_at')
    list_filter = ('is_active', 'stock_item__category')
    search_fields = ('name', 'stock_item__name', 'description')
    list_editable = ('sale_price', 'is_active') # Permite editar direto na lista
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ['stock_item'] # Facilita a seleção do item de estoque

    fieldsets = (
        (None, {'fields': ('name', 'stock_item', 'is_active')}),
        ('Detalhes do Cardápio', {'fields': ('description', 'sale_price', 'image')}),
        ('Datas', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)})
    )

    @admin.display(description='Item de Estoque')
    def stock_item_link(self, obj):
        # Cria um link para o item de estoque no admin, se ele existir
        if obj.stock_item:
            from django.urls import reverse
            link = reverse("admin:stock_stockitem_change", args=[obj.stock_item.id])
            return format_html('<a href="{}">{}</a>', link, obj.stock_item.name)
        return "Nenhum"
    stock_item_link.admin_order_field = 'stock_item' # Permite ordenar por este campo