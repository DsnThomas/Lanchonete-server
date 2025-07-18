# orders/admin.py
from django.contrib import admin
from .models import Venda, ItemVenda

class ItemVendaInline(admin.TabularInline):
    model = ItemVenda
    fields = ('produto', 'nome_produto', 'quantidade', 'preco_unitario', 'subtotal')
    readonly_fields = ('nome_produto', 'preco_unitario', 'subtotal')
    extra = 0 # Não mostra campos vazios para adicionar

@admin.register(Venda)
class VendaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'data_venda', 'valor_total', 'status')
    list_filter = ('status', 'data_venda')
    search_fields = ('id', 'cliente__email')
    readonly_fields = ('id', 'data_venda', 'valor_total')
    inlines = [ItemVendaInline] # Mostra os itens dentro da página da venda