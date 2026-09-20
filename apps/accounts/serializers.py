from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Empleado, Modulo, Perfil, Permiso, Usuario, UsuarioPerfil


class LoginRequestSerializer(serializers.Serializer):
    usuario = serializers.CharField()
    password = serializers.CharField(write_only=True)


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    usuario = serializers.DictField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)


class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])


class RoleAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioPerfil
        fields = ("profile", "company", "branch", "is_active")

    def validate(self, attrs):
        branch = attrs.get("branch")
        company = attrs.get("company")
        if branch and branch.empresa_id != company.pk:
            raise serializers.ValidationError({"branch": "La sucursal no pertenece a la empresa indicada."})
        return attrs


class SetRolesSerializer(serializers.Serializer):
    roles = RoleAssignmentSerializer(many=True, allow_empty=True)

    def validate_roles(self, roles):
        keys = [(item["profile"].pk, item["company"].pk, item.get("branch").pk if item.get("branch") else None) for item in roles]
        if len(keys) != len(set(keys)):
            raise serializers.ValidationError("No se permiten roles duplicados en el mismo ámbito.")
        return roles


class PermissionMatrixItemSerializer(serializers.Serializer):
    module = serializers.PrimaryKeyRelatedField(queryset=Modulo.objects.all())
    can_view = serializers.BooleanField(default=False)
    can_create = serializers.BooleanField(default=False)
    can_update = serializers.BooleanField(default=False)
    can_delete = serializers.BooleanField(default=False)
    can_approve = serializers.BooleanField(default=False)
    can_cancel = serializers.BooleanField(default=False)
    can_close = serializers.BooleanField(default=False)
    can_export = serializers.BooleanField(default=False)


class PermissionMatrixSerializer(serializers.Serializer):
    permissions = PermissionMatrixItemSerializer(many=True, allow_empty=True)

    def validate_permissions(self, permissions):
        modules = [item["module"].pk for item in permissions]
        if len(modules) != len(set(modules)):
            raise serializers.ValidationError("Cada módulo debe aparecer una sola vez.")
        return permissions


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    roles = RoleAssignmentSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "first_name", "last_name", "is_active", "must_change_password", "password", "roles")
        read_only_fields = ("must_change_password",)

    def validate(self, attrs):
        if self.instance is None and not attrs.get("password"):
            raise serializers.ValidationError({"password": "La clave temporal es obligatoria."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = Usuario(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class EmpleadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empleado
        fields = "__all__"


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = "__all__"


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = "__all__"


class PermisoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permiso
        fields = "__all__"


class MeSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    employee = EmpleadoSerializer(source="empleado", read_only=True)

    class Meta:
        model = Usuario
        fields = ("id", "username", "email", "first_name", "last_name", "employee", "permissions")

    def get_permissions(self, obj) -> list[str]:
        if obj.is_superuser:
            return ["*"]
        permissions = Permiso.objects.filter(profile__user_roles__user=obj, profile__user_roles__is_active=True).select_related("module")
        result = []
        for permission in permissions:
            for field in ("view", "create", "update", "delete", "approve", "cancel", "close", "export"):
                if getattr(permission, f"can_{field}"):
                    result.append(f"{permission.module.code}.{field}")
        return sorted(set(result))
