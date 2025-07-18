# users/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.contrib.auth import authenticate, get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
# ALTERADO: Trocamos DestroyAPIView pela view mais completa
from rest_framework.generics import RetrieveUpdateDestroyAPIView 
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import CustomUser, Cargo, PasswordResetCode, FrontendPermission
from .serializers import (
    UserRegisterSerializer, 
    UserLoginSerializer, 
    EmployeeRegisterSerializer,
    UserSerializer, 
    CargoSerializer,
    # IMPORTADO o novo serializer de atualização
    EmployeeUpdateSerializer, 
    PasswordResetRequestSerializer, 
    PasswordResetConfirmSerializer,
    FrontendPermissionSerializer
)
from django.core.mail import send_mail
from django.conf import settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action


CustomUser = get_user_model()


# --- Permissão Customizada para Usuários da Equipe ---
class IsEquipe(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'equipe'
    


class FrontendPermissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint para listar as permissões do painel disponíveis.
    Acessível apenas por membros da equipe.
    """
    queryset = FrontendPermission.objects.all()
    serializer_class = FrontendPermissionSerializer
    permission_classes = [IsAuthenticated, IsEquipe]

# --- VIEWSET PARA GERENCIAR CARGOS ---
class CargoViewSet(viewsets.ModelViewSet):
    """
    API endpoint que permite visualizar, criar, editar e deletar Cargos.
    Acessível apenas por membros da equipe.
    """
    queryset = Cargo.objects.all().order_by('name')
    serializer_class = CargoSerializer
    permission_classes = [IsAuthenticated, IsEquipe]

    # --- AÇÃO ADICIONADA PARA ATRIBUIR PERMISSÕES ---
    @action(detail=True, methods=['post'], url_path='set-permissions')
    def set_permissions(self, request, pk=None):
        cargo = self.get_object()
        permission_ids = request.data.get('permission_ids', [])

        if not isinstance(permission_ids, list):
            return Response(
                {'error': 'permission_ids deve ser uma lista de IDs.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            permissions = FrontendPermission.objects.filter(id__in=permission_ids)
            if len(permissions) != len(permission_ids):
                 return Response(
                    {'error': 'Um ou mais IDs de permissão são inválidos.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception:
            return Response(
                {'error': 'Erro ao processar os IDs de permissão.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        cargo.permissions.set(permissions)
        serializer = self.get_serializer(cargo)
        return Response(serializer.data, status=status.HTTP_200_OK)


# --- Views de Autenticação existentes ---
class RegisterView(APIView):
    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({'message': 'Usuário registrado com sucesso!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            # --- LÓGICA DE PERMISSÃO ATUALIZADA ---
            function_name = None
            permissions_codenames = []
            if user.role == 'equipe' and user.function:
                function_name = user.function.name
                # Pega todos os codenames das permissões associadas ao cargo do usuário
                permissions_codenames = list(user.function.permissions.values_list('codename', flat=True))
            
            # Admins e superusers têm todas as permissões
            if user.is_superuser or user.role == 'admin':
                permissions_codenames = ['all']

            return Response({
                'message': f'Login bem-sucedido como {user.role}!',
                'user': {
                    'id': user.id,
                    'first_name': user.first_name,
                    'email': user.email,
                    'role': user.role,
                    'function_name': function_name,
                    # --- DADO DE PERMISSÕES ADICIONADO ---
                    'permissions': permissions_codenames
                },
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- View para Cadastro de Funcionários (Protegida) ---
class RegisterEmployeeView(APIView):
    permission_classes = [IsAuthenticated, IsEquipe]

    def post(self, request):
        mutable_data = request.data.copy()
        mutable_data['role'] = 'equipe'
        
        if 'email' not in mutable_data or not mutable_data['email']:
            base_email_name = mutable_data.get('first_name', 'funcionario_temp').replace(' ', '.').lower()
            mutable_data['email'] = f"{base_email_name}_{CustomUser.objects.count()}@unifucamp.edu.br" 

        if 'password2' not in mutable_data:
            mutable_data['password2'] = mutable_data.get('password')

        serializer = EmployeeRegisterSerializer(data=mutable_data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(user)
            return Response({'message': 'Funcionário registrado com sucesso!', 'user': response_serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# --- VIEW: Listar Funcionários da Equipe (Protegida) ---
class EmployeeListView(APIView):
    permission_classes = [IsAuthenticated, IsEquipe] 

    def get(self, request):
        employees = CustomUser.objects.filter(role='equipe').order_by('first_name')
        serializer = UserSerializer(employees, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# --- VIEW SUBSTITUÍDA: Gerencia GET, UPDATE e DELETE de um funcionário ---
class EmployeeDetailView(RetrieveUpdateDestroyAPIView):
    """
    View para ler, atualizar e deletar um funcionário específico.
    """
    queryset = CustomUser.objects.filter(role='equipe')
    permission_classes = [IsAuthenticated, IsEquipe]
    lookup_field = 'id'

    def get_serializer_class(self):
        # Usa UserSerializer para GET (para incluir o nome do cargo)
        if self.request.method == 'GET':
            return UserSerializer
        # Usa EmployeeUpdateSerializer para PUT/PATCH (para não exigir senha, etc.)
        return EmployeeUpdateSerializer

    def perform_destroy(self, instance):
        # Lógica para impedir que um usuário se delete
        if self.request.user.id == instance.id:
            raise PermissionDenied("Você não pode deletar sua própria conta através desta interface.")
        super().perform_destroy(instance)


# --- Views de Teste (mantidas) ---
class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        content = {
            'message': f'Olá, {request.user.first_name if request.user.first_name else request.user.email}! Você está autenticado.',
            'user_id': request.user.id,
            'user_role': request.user.role
        }
        return Response(content)

class EquipeOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsEquipe]

    def get(self, request):
        content = {
            'message': f'Bem-vindo, {request.user.first_name if request.user.first_name else request.user.email} da equipe! Você tem acesso a este recurso restrito.',
            'user_id': request.user.id,
            'user_role': request.user.role
        }
        return Response(content)

# --- Views de Redefinição de Senha ---
class RequestPasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user_instance'] 
            
            PasswordResetCode.objects.filter(user=user).delete()
            reset_code_instance = PasswordResetCode.objects.create(user=user)
            
            subject = 'Seu Código de Redefinição de Senha - Espaço Lanches'
            message = (
                f'Olá {user.first_name or user.email.split("@")[0]},\n\n'
                f'Você solicitou a redefinição de senha para sua conta no Espaço Lanches.\n'
                f'Use o seguinte código para criar uma nova senha:\n\n'
                f'{reset_code_instance.code}\n\n'
                f'Este código é válido por 1 hora.\n'
                f'Se você não solicitou esta redefinição, por favor, ignore este e-mail.\n\n'
                'Atenciosamente,\nEquipe Espaço Lanches'
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'nao-responda@espacolanches.com')
            
            try:
                send_mail(subject, message, from_email, [user.email])
                return Response({'message': 'Um código de redefinição foi enviado para o seu e-mail.'}, status=status.HTTP_200_OK)
            except Exception as e:
                print(f"Erro ao enviar email: {e}") 
                return Response({'message': 'Ocorreu um problema ao tentar enviar o e-mail de redefinição. Tente novamente mais tarde.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ConfirmPasswordResetView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            new_password = serializer.validated_data['password']
            reset_code_instance = serializer.validated_data['reset_code_instance']

            user.set_password(new_password)
            user.save()
            
            reset_code_instance.delete()

            return Response({'message': 'Sua senha foi redefinida com sucesso! Você já pode fazer login com a nova senha.'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)