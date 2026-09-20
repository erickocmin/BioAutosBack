from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

from common.permissions import HasModulePermission
from common.viewsets import AuditedModelViewSet
from .models import Empresa, Oficina, SerieDocumento, Sucursal, TipoDocumento, Ubigeo
from .serializers import EmpresaSerializer, OficinaSerializer, SerieDocumentoSerializer, SucursalSerializer, TipoDocumentoSerializer, UbigeoSerializer


class BaseCoreViewSet(AuditedModelViewSet):
    permission_classes = [HasModulePermission]


class EmpresaViewSet(BaseCoreViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_module = "core.empresas"
    scope_company_lookup = ""
    search_fields = ["ruc", "razon_social", "nombre_comercial"]
    ordering_fields = ["razon_social", "created_at"]


class SucursalViewSet(BaseCoreViewSet):
    queryset = Sucursal.objects.select_related("empresa")
    serializer_class = SucursalSerializer
    permission_module = "core.sucursales"
    scope_branch_lookup = ""
    filterset_fields = ["empresa", "activa"]
    search_fields = ["codigo", "nombre"]


class OficinaViewSet(BaseCoreViewSet):
    queryset = Oficina.objects.select_related("sucursal", "sucursal__empresa").order_by("sucursal_id", "nombre")
    serializer_class = OficinaSerializer
    permission_module = "core.oficinas"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["sucursal", "activa"]
    search_fields = ["codigo", "nombre"]


class UbigeoViewSet(BaseCoreViewSet):
    http_method_names = ["get", "head", "options"]
    queryset = Ubigeo.objects.all()
    serializer_class = UbigeoSerializer
    permission_module = "core.ubigeo"
    filterset_fields = ["departamento", "provincia"]
    search_fields = ["codigo_inei", "departamento", "provincia", "distrito"]


class TipoDocumentoViewSet(BaseCoreViewSet):
    queryset = TipoDocumento.objects.order_by("nombre")
    serializer_class = TipoDocumentoSerializer
    permission_module = "core.tipos_documento"
    search_fields = ["codigo", "nombre", "codigo_sunat"]


class SerieDocumentoViewSet(BaseCoreViewSet):
    queryset = SerieDocumento.objects.select_related("empresa", "sucursal", "tipo_documento").order_by("sucursal_id", "tipo_documento_id", "serie")
    serializer_class = SerieDocumentoSerializer
    permission_module = "core.series_documento"
    scope_branch_lookup = "sucursal"
    filterset_fields = ["empresa", "sucursal", "tipo_documento", "activa"]

    @action(detail=True, methods=["post"], permission_classes=[HasModulePermission])
    def siguiente(self, request, pk=None):
        self.permission_action = "can_create"
        serie, numero = SerieDocumento.issue_next(pk)
        return Response({"serie": serie, "numero": numero})


@extend_schema(responses=inline_serializer(name="MenuItem", many=True, fields={
    "code": serializers.CharField(), "name": serializers.CharField(),
    "route": serializers.CharField(), "icon": serializers.CharField(),
}))
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def menu(request):
    from apps.accounts.models import Modulo
    if request.user.is_superuser:
        modules = Modulo.objects.filter(is_active=True)
    else:
        modules = Modulo.objects.filter(permissions__profile__user_roles__user=request.user, permissions__can_view=True).distinct()
    return Response([{"code": item.code, "name": item.name, "route": item.route, "icon": item.icon} for item in modules])
