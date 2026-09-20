from rest_framework import status
from django.db import transaction
from rest_framework.decorators import action, api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema

from common.permissions import HasModulePermission
from common.viewsets import AuditedModelViewSet
from .models import Empleado, Modulo, Perfil, Permiso, Usuario, UsuarioPerfil
from .serializers import (EmpleadoSerializer, LoginRequestSerializer, LoginResponseSerializer, LogoutSerializer,
                          MeSerializer, ModuloSerializer, PerfilSerializer, PermissionMatrixSerializer,
                          PermisoSerializer, ResetPasswordSerializer, SetRolesSerializer, UsuarioSerializer)
from common.services import audit


class LoginThrottle(ScopedRateThrottle):
    scope = "login"


@extend_schema(request=LoginRequestSerializer, responses=LoginResponseSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
def login(request):
    serializer = TokenObtainPairSerializer(data={"username": request.data.get("usuario"), "password": request.data.get("password")})
    serializer.is_valid(raise_exception=True)
    user = Usuario.objects.get(username=request.data.get("usuario"))
    return Response({**serializer.validated_data, "usuario": MeSerializer(user).data})


@extend_schema(request=LogoutSerializer, responses={205: None})
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    token = request.data.get("refresh")
    if not token:
        return Response({"code": "refresh_required", "message": "Se requiere refresh token."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        RefreshToken(token).blacklist()
    except TokenError:
        return Response({"code": "invalid_refresh", "message": "El refresh token no es válido o ya fue revocado."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_205_RESET_CONTENT)


@extend_schema(responses=MeSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(MeSerializer(request.user).data)


class UsuarioViewSet(AuditedModelViewSet):
    queryset = Usuario.objects.select_related("empleado", "empleado__sucursal")
    serializer_class = UsuarioSerializer
    permission_classes = [HasModulePermission]
    permission_module = "accounts.usuarios"
    scope_branch_lookup = "empleado__sucursal"
    filterset_fields = ["is_active"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "date_joined"]

    @action(detail=True, methods=["post"], url_path="restablecer-clave")
    def reset_password(self, request, pk=None):
        serializer = ResetPasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = self.get_object()
        user.set_password(serializer.validated_data["password"])
        user.must_change_password = True
        user.save(update_fields=["password", "must_change_password"])
        audit(actor=request.user, action="reset_password", instance=user, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["put"], url_path="roles")
    @transaction.atomic
    def set_roles(self, request, pk=None):
        serializer = SetRolesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_object()
        user.roles.all().delete()
        roles = []
        for item in serializer.validated_data["roles"]:
            branch = item.get("branch")
            roles.append(UsuarioPerfil(user=user, scope_key=f"branch:{branch.pk}" if branch else "global", **item))
        UsuarioPerfil.objects.bulk_create(roles)
        audit(actor=request.user, action="set_roles", instance=user, request=request)
        return Response(SetRolesSerializer({"roles": user.roles.all()}).data)


class EmpleadoViewSet(AuditedModelViewSet):
    queryset = Empleado.objects.select_related("usuario", "sucursal", "sucursal__empresa").order_by("apellidos", "nombres")
    serializer_class = EmpleadoSerializer
    permission_classes = [HasModulePermission]
    permission_module = "accounts.empleados"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["sucursal", "activo"]
    search_fields = ["codigo", "numero_documento", "nombres", "apellidos", "biometric_pin"]


class PerfilViewSet(AuditedModelViewSet):
    queryset = Perfil.objects.order_by("nombre")
    serializer_class = PerfilSerializer
    permission_classes = [HasModulePermission]
    permission_module = "accounts.perfiles"

    @action(detail=True, methods=["put"], url_path="matriz-permisos")
    @transaction.atomic
    def set_permissions(self, request, pk=None):
        serializer = PermissionMatrixSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = self.get_object()
        profile.permissions.all().delete()
        Permiso.objects.bulk_create([Permiso(profile=profile, **item) for item in serializer.validated_data["permissions"]])
        audit(actor=request.user, action="set_permissions", instance=profile, request=request)
        return Response(PermisoSerializer(profile.permissions.select_related("module"), many=True).data)


class ModuloViewSet(AuditedModelViewSet):
    queryset = Modulo.objects.select_related("parent")
    serializer_class = ModuloSerializer
    permission_classes = [HasModulePermission]
    permission_module = "accounts.modulos"


class PermisoViewSet(AuditedModelViewSet):
    queryset = Permiso.objects.select_related("profile", "module").order_by("profile_id", "module_id")
    serializer_class = PermisoSerializer
    permission_classes = [HasModulePermission]
    permission_module = "accounts.permisos"
    filterset_fields = ["profile", "module"]
