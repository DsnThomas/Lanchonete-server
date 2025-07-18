# users/models.py
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
import random
from datetime import timedelta

class FrontendPermission(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome da Permissão")
    codename = models.CharField(max_length=100, unique=True, verbose_name="Codename (identificador da seção)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Permissão do Painel"
        verbose_name_plural = "Permissões do Painel"
        ordering = ['name']

# --- MODELO CARGO ---
class Cargo(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome do Cargo")
    # --- CAMPO ADICIONADO ---
    permissions = models.ManyToManyField(
        FrontendPermission,
        blank=True,
        verbose_name="Permissões no Painel"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"
        ordering = ['name']


# --- CustomUserManager ---
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('role', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        if 'first_name' not in extra_fields or not extra_fields['first_name']:
            raise ValueError(_('Superuser must have a first_name.'))
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    USER_ROLES = (
        ('estudante', 'Estudante'),
        ('equipe', 'Equipe'),
        ('admin', 'Administrador'),
    )
    role = models.CharField(max_length=20, choices=USER_ROLES, default='estudante')
    username = models.CharField(_("username"), max_length=150, unique=False, blank=True, null=True, help_text=_("Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."), error_messages={"unique": _("A user with that username already exists."),},)
    email = models.EmailField(_("email address"), unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'role']
    objects = CustomUserManager()

    # --- CAMPOS DE FUNCIONÁRIO COM ENDEREÇO SEPARADO ---
    cpf = models.CharField(max_length=14, unique=True, null=True, blank=True)
    
    # REMOVIDO: O campo de endereço antigo
    # address = models.TextField(max_length=255, null=True, blank=True)
    
    # ADICIONADO: Novos campos de endereço
    street = models.CharField(max_length=150, blank=True, null=True, verbose_name="Rua")
    number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Número")
    neighborhood = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Cidade")

    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    function = models.ForeignKey(
        Cargo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Cargo"
    )
    phone = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    admission_date = models.DateField(null=True, blank=True)
    SHIFT_CHOICES = (('manha', 'Manhã'), ('tarde', 'Tarde'), ('noite', 'Noite'), ('integral', 'Integral'),)
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES, null=True, blank=True)
    MARITAL_STATUS_CHOICES = (('solteiro', 'Solteiro(a)'), ('casado', 'Casado(a)'), ('divorciado', 'Divorciado(a)'), ('viuvo', 'Viúvo(a)'), ('uniao_estavel', 'União Estável'),)
    marital_status = models.CharField(max_length=15, choices=MARITAL_STATUS_CHOICES, null=True, blank=True)

    def __str__(self):
        return self.first_name if self.first_name else self.email

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['email']


# --- PasswordResetCode (sem alterações) ---
class PasswordResetCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=6, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = "%06d" % random.randint(0, 999999)
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Código {self.code} para {self.user.email} (expira em {self.expires_at.strftime('%Y-%m-%d %H:%M')})"

    class Meta:
        verbose_name = "Código de Redefinição de Senha"
        verbose_name_plural = "Códigos de Redefinição de Senha"
        ordering = ['-created_at']