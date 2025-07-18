# users/serializers.py
from rest_framework import serializers
from .models import CustomUser, Cargo, FrontendPermission
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import PasswordResetCode
from django.utils import timezone

class FrontendPermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrontendPermission
        fields = ['id', 'name', 'codename']

# --- NOVO SERIALIZER PARA CARGOS ---
class CargoSerializer(serializers.ModelSerializer):
    # Mostra os objetos de permissão completos ao listar cargos
    permissions = FrontendPermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Cargo
        fields = ['id', 'name', 'permissions']


# --- UserRegisterSerializer (sem alterações de endereço, pois é para estudantes) ---
class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['first_name', 'email', 'password', 'password2', 'role']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def validate_email(self, value):
        if not value.endswith('@unifucamp.edu.br'):
            raise serializers.ValidationError("Por favor, utilize um e-mail com o domínio @unifucamp.edu.br.")
        return value

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não conferem."})
        try:
            validate_password(data['password'], user=None)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = CustomUser.objects.create_user(
            username=validated_data.get('email'), 
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            role=validated_data['role']
        )
        return user


# --- EmployeeRegisterSerializer (ALTERADO) ---
class EmployeeRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        # ALTERADO: 'address' foi substituído pelos novos campos
        fields = [
            'first_name', 'email', 'password', 'password2', 'role',
            'cpf', 'street', 'number', 'neighborhood', 'city', 'salary', 'function',
            'phone', 'date_of_birth', 'admission_date', 'shift', 'marital_status'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'function': {'required': True, 'allow_null': False},
            # Definindo campos como opcionais
            'cpf': {'required': False, 'allow_null': True},
            'salary': {'required': False, 'allow_null': True},
            'phone': {'required': False, 'allow_null': True},
            'date_of_birth': {'required': False, 'allow_null': True},
            'admission_date': {'required': False, 'allow_null': True},
            'shift': {'required': False, 'allow_null': True},
            'marital_status': {'required': False, 'allow_null': True},
            # Definindo novos campos de endereço como opcionais
            'street': {'required': False, 'allow_null': True},
            'number': {'required': False, 'allow_null': True},
            'neighborhood': {'required': False, 'allow_null': True},
            'city': {'required': False, 'allow_null': True},
        }

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "As senhas não conferem."})
        try:
            validate_password(data['password'], user=None)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        data['username'] = data['email'] 
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        # O método create_user com **validated_data já lida com os novos campos automaticamente
        user = CustomUser.objects.create_user(**validated_data)
        return user


# --- UserLoginSerializer (sem alterações) ---
class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    role = serializers.CharField(required=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError("Credenciais inválidas ou usuário não encontrado.")
        else:
            raise serializers.ValidationError("E-mail e senha são obrigatórios.")
        if user.role != role:
            raise serializers.ValidationError(f"Acesso negado. Função esperada: {role}, função do usuário: {user.role}.")
        data['user'] = user
        return data


# --- UserSerializer (ALTERADO para listagem de funcionários) ---
class UserSerializer(serializers.ModelSerializer):
    function_name = serializers.CharField(source='function.name', read_only=True, allow_null=True)

    class Meta:
        model = CustomUser
        # ALTERADO: substituímos 'address' pelos novos campos
        fields = [
            'id', 'first_name', 'last_name', 'email', 'role',
            'cpf', 'street', 'number', 'neighborhood', 'city', 
            'salary', 'function', 'function_name',
            'phone', 'date_of_birth', 'admission_date', 'shift', 'marital_status'
        ]

# --- EmployeeUpdateSerializer (ALTERADO) ---
class EmployeeUpdateSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = CustomUser
        # ALTERADO: substituímos 'address' pelos novos campos
        fields = [
            'first_name', 'last_name', 'email', 'cpf', 
            'street', 'number', 'neighborhood', 'city', 
            'salary', 'function', 'phone', 'date_of_birth', 
            'admission_date', 'shift', 'marital_status'
        ]
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }

# --- Serializers de Redefinição de Senha (sem alterações) ---
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate(self, data):
        email = data.get('email')
        try:
            user = CustomUser.objects.get(email=email)
            data['user_instance'] = user
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError({"email": "Nenhum usuário encontrado com este endereço de e-mail."})
        return data

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, max_length=64)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        code_value = data.get('code')
        password = data.get('password')
        password2 = data.get('password2')
        if password != password2:
            raise serializers.ValidationError({"password": "As senhas não conferem."})
        try:
            validate_password(password, user=None)
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        try:
            reset_code_instance = PasswordResetCode.objects.get(user__email=email, code=code_value)
            if reset_code_instance.expires_at < timezone.now():
                reset_code_instance.delete()
                raise serializers.ValidationError({"code": "Este código de redefinição expirou."})
        except PasswordResetCode.DoesNotExist:
            raise serializers.ValidationError({"code": "Código de redefinição inválido ou não encontrado para este e-mail."})
        data['user'] = reset_code_instance.user
        data['reset_code_instance'] = reset_code_instance
        return data