from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Max
from rest_framework import mixins, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import OpenApiTypes, extend_schema

from common.permissions import HasModulePermission
from common.viewsets import AuditedModelViewSet
from common.scoping import ScopedQuerysetMixin
from .models import AttendanceDevice, AttendanceEvent, DailyAttendance
from .filters import DailyAttendanceFilter, EventFilter
from .serializers import DailyAttendanceSerializer, DeviceSerializer, EventListSerializer, EventSerializer
from .services import receive_attlog


@extend_schema(request=OpenApiTypes.BYTE, responses=OpenApiTypes.STR)
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def iclock_cdata(request):
    serial = request.query_params.get("SN") or request.query_params.get("sn")
    try:
        device = AttendanceDevice.objects.get(serial_number=serial, status=AttendanceDevice.Status.ACTIVE)
    except AttendanceDevice.DoesNotExist:
        return HttpResponse("ERROR: unknown device", status=403, content_type="text/plain")
    device.last_connection = timezone.now()
    if request.META.get("REMOTE_ADDR"):
        device.ip_address = request.META["REMOTE_ADDR"]
    device.save(update_fields=["last_connection", "ip_address", "updated_at"])
    if request.method == "GET":
        return HttpResponse(f"GET OPTION FROM: {serial}\nStamp=0\nOpStamp=0\nErrorDelay=30\nDelay=10\nTransTimes=00:00;14:05\nTransInterval=1\nTransFlag=1111000000", content_type="text/plain")
    created, duplicates = receive_attlog(device=device, raw_body=request.body.decode("utf-8", errors="replace"))
    return HttpResponse(f"OK: {len(created)} duplicate: {duplicates}", content_type="text/plain")


class DeviceViewSet(AuditedModelViewSet):
    queryset = AttendanceDevice.objects.select_related("branch", "branch__empresa").annotate(last_marking=Max("events__occurred_at")).order_by("name")
    serializer_class = DeviceSerializer
    permission_classes = [HasModulePermission]
    permission_module = "attendance.devices"
    scope_branch_lookup = "branch"
    filterset_fields = ["branch", "status"]
    search_fields = ["serial_number", "name", "device_model", "location"]


class EventViewSet(ScopedQuerysetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = AttendanceEvent.objects.select_related("device", "employee", "employee__sucursal").order_by("-occurred_at", "-id")
    serializer_class = EventSerializer
    permission_classes = [HasModulePermission]
    permission_module = "attendance.events"
    scope_branch_lookup = "device__branch"
    filterset_class = EventFilter
    ordering_fields = ["occurred_at", "received_at"]

    def get_serializer_class(self):
        return EventListSerializer if self.action == "list" else EventSerializer


class DailyAttendanceViewSet(ScopedQuerysetMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = DailyAttendance.objects.select_related("employee", "employee__sucursal").order_by("-date", "employee_id")
    serializer_class = DailyAttendanceSerializer
    permission_classes = [HasModulePermission]
    permission_module = "attendance.daily"
    scope_branch_lookup = "employee__sucursal"
    filterset_class = DailyAttendanceFilter
    ordering_fields = ["date", "worked_minutes"]
