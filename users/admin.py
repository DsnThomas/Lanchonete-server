# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Cargo, FrontendPermission

@admin.register(FrontendPermission)
class FrontendPermissionAdmin(admin.ModelAdmin):
    """
    Configuração para exibir o modelo FrontendPermission no painel admin.
    """
    list_display = ('name', 'codename')
    search_fields = ('name', 'codename')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    """
    Configuração para exibir o modelo Cargo no painel admin.
    """
    list_display = ('name',)
    search_fields = ('name',)
    filter_horizontal = ('permissions',)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Configuração personalizada para o modelo CustomUser no painel admin.
    """
    # Campos que aparecerão na lista de usuários no admin
    list_display = (
        'email', 'first_name', 'role', 'is_staff', 'is_active',
        'phone', 'cpf', 'function', 'city' # ALTERADO: Mostrando a cidade na lista
    )
    
    # Campos que aparecerão nos formulários de criação/edição de usuário
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (('Informações Pessoais'), {'fields': ('first_name', 'last_name', 'phone', 'date_of_birth', 'marital_status')}),
        # ALTERADO: 'address' foi substituído pelos novos campos agrupados
        (('Informações de Funcionário'), {'fields': ('role', 'cpf', ('street', 'number'), ('neighborhood', 'city'), 'salary', 'function', 'shift', 'admission_date')}),
        (('Permissões'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (('Datas Importantes'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Campos para o formulário de adição de novo usuário
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # ALTERADO: 'address' foi substituído pelos novos campos
            'fields': (
                'email', 'first_name', 'last_name', 'password', 'password2', 'role',
                'phone', 'date_of_birth', 'admission_date', 'shift', 'marital_status',
                'cpf', 'street', 'number', 'neighborhood', 'city', 'salary', 'function'
            ),
        }),
    )
    
    # Campos que podem ser pesquisados
    # ADICIONADO: Novos campos de endereço para a busca
    search_fields = ('email', 'first_name', 'last_name', 'cpf', 'phone', 'function__name', 'street', 'neighborhood', 'city')
    
    # Campos que podem ser usados para filtrar a lista
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role', 'shift', 'marital_status', 'function')

    # Ordenação padrão da lista
    ordering = ('email',)