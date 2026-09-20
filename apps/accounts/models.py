from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models

from common.models import TimeStampedModel


document_validator = RegexValidator(r"^[0-9]{8,11}$", "El documento debe tener entre 8 y 11 dígitos.")


class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    must_change_password = models.BooleanField(default=False)

    class Meta:
        ordering = ["username"]


class Empleado(TimeStampedModel):
    usuario = models.OneToOneField(Usuario, related_name="empleado", null=True, blank=True, on_delete=models.SET_NULL)
    sucursal = models.ForeignKey("core.Sucursal", related_name="empleados", on_delete=models.PROTECT)
    codigo = models.CharField(max_length=30, unique=True)
    numero_documento = models.CharField(max_length=11, validators=[document_validator], db_index=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=120)
    cargo = models.CharField(max_length=100, blank=True)
    biometric_pin = models.CharField(max_length=32, unique=True, null=True, blank=True)
    activo = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=["sucursal", "activo"]), models.Index(fields=["apellidos", "nombres"])]

    def __str__(self):
        return f"{self.apellidos}, {self.nombres}"


class Perfil(TimeStampedModel):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)


class Modulo(TimeStampedModel):
    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    route = models.CharField(max_length=200, blank=True)
    icon = models.CharField(max_length=50, blank=True)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.PROTECT)
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]


class Permiso(models.Model):
    profile = models.ForeignKey(Perfil, related_name="permissions", on_delete=models.CASCADE)
    module = models.ForeignKey(Modulo, related_name="permissions", on_delete=models.CASCADE)
    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_cancel = models.BooleanField(default=False)
    can_close = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["profile", "module"], name="uq_permiso_perfil_modulo")]


class UsuarioPerfil(models.Model):
    user = models.ForeignKey(Usuario, related_name="roles", on_delete=models.CASCADE)
    profile = models.ForeignKey(Perfil, related_name="user_roles", on_delete=models.PROTECT)
    company = models.ForeignKey("core.Empresa", related_name="user_roles", on_delete=models.PROTECT)
    branch = models.ForeignKey("core.Sucursal", related_name="user_roles", null=True, blank=True, on_delete=models.PROTECT)
    scope_key = models.CharField(max_length=32, editable=False, default="global")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "profile", "company", "scope_key"], name="uq_usuario_perfil_contexto")]
        indexes = [models.Index(fields=["user", "is_active"]), models.Index(fields=["company", "branch"])]

    def save(self, *args, **kwargs):
        self.scope_key = f"branch:{self.branch_id}" if self.branch_id else "global"
        super().save(*args, **kwargs)
