# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView,
    LoginView,
    RegisterEmployeeView,
    EmployeeListView,
    EmployeeDetailView,  # CORRIGIDO: Importa a view correta
    ProtectedView,
    EquipeOnlyView,
    RequestPasswordResetView,
    ConfirmPasswordResetView,
    CargoViewSet,
    FrontendPermissionViewSet
)

# 1. Cria um router
router = DefaultRouter()
# 2. Registra a CargoViewSet na rota 'roles'
router.register(r'roles', CargoViewSet, basename='cargo')

router.register(r'frontend-permissions', FrontendPermissionViewSet, basename='frontend-permission')

# 3. Adiciona as rotas do router ao urlpatterns
urlpatterns = [
    # Inclui as rotas geradas automaticamente para a API de Cargos
    path('', include(router.urls)),

    # Rotas de Autenticação Básica
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    # Rotas de Funcionários
    path('register-employee/', RegisterEmployeeView.as_view(), name='register_employee'),
    path('employees/', EmployeeListView.as_view(), name='employee_list'),
    
    # CORRIGIDO: Esta rota agora usa a EmployeeDetailView para GET, PATCH e DELETE
    path('employees/<int:id>/', EmployeeDetailView.as_view(), name='employee_detail'),

    # Rotas de Redefinição de Senha
    path('password-reset/request/', RequestPasswordResetView.as_view(), name='request_password_reset'),
    path('password-reset/confirm/', ConfirmPasswordResetView.as_view(), name='confirm_password_reset'),

    # Rotas de teste
    path('protected/', ProtectedView.as_view(), name='protected_view'),
    path('equipe-only/', EquipeOnlyView.as_view(), name='equipe_only_view'),
]