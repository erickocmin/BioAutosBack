import re

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Max
from rest_framework import generics, mixins, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiTypes, extend_schema

from common.permissions import HasModulePermission
from common.viewsets import AuditedModelViewSet
from common.scoping import ScopedQuerysetMixin
from .models import AttendanceDevice, AttendanceEvent, DailyAttendance, DeviceCommand
from .filters import DailyAttendanceFilter, EventFilter
from .serializers import DailyAttendanceSerializer, DeviceSerializer, EventListSerializer, EventSerializer, LocalEnrollmentSerializer
from .services import is_private_client_ip, local_ipv4_addresses, process_event, receive_attlog, test_device_tcp_connection


def _device_for_request(request):
    client_ip = request.META.get("REMOTE_ADDR", "")
    if not getattr(settings, "ATTENDANCE_ALLOW_PUBLIC_DEVICE_IPS", False) and not is_private_client_ip(client_ip):
        return None
    serial = request.query_params.get("SN") or request.query_params.get("sn")
    try:
        return AttendanceDevice.objects.get(serial_number=serial, status=AttendanceDevice.Status.ACTIVE)
    except AttendanceDevice.DoesNotExist:
        return None


def _touch_device(device, request):
    device.last_connection = timezone.now()
    client_ip = request.META.get("REMOTE_ADDR")
    if client_ip and is_private_client_ip(client_ip):
        device.ip_address = client_ip
    firmware = request.query_params.get("FWVersion") or request.query_params.get("pushver")
    if firmware:
        device.firmware = firmware[:100]
    device.save(update_fields=["last_connection", "ip_address", "firmware", "updated_at"])


@extend_schema(request=OpenApiTypes.BYTE, responses=OpenApiTypes.STR)
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def iclock_cdata(request):
    device = _device_for_request(request)
    if not device:
        return HttpResponse("ERROR: unknown device", status=403, content_type="text/plain")
    _touch_device(device, request)
    if request.method == "GET":
        return HttpResponse(
            f"GET OPTION FROM: {device.serial_number}\nStamp=0\nOpStamp=0\nErrorDelay=30\nDelay=10\n"
            "TransTimes=00:00;14:05\nTransInterval=1\nTransFlag=1111000000\nRealtime=1\nPushVersion=2.4.1",
            content_type="text/plain",
        )
    table = (request.query_params.get("table") or "ATTLOG").upper()
    if table != "ATTLOG":
        return HttpResponse("OK", content_type="text/plain")
    created, duplicates = receive_attlog(device=device, raw_body=request.body.decode("utf-8", errors="replace"))
    for event in created:
        if event.employee_id:
            process_event(event)
    return HttpResponse(f"OK: {len(created)} duplicate: {duplicates}", content_type="text/plain")


@extend_schema(responses=OpenApiTypes.STR)
@api_view(["GET"])
@permission_classes([AllowAny])
def iclock_getrequest(request):
    device = _device_for_request(request)
    if not device:
        return HttpResponse("ERROR: unknown device", status=403, content_type="text/plain")
    _touch_device(device, request)
    command = device.commands.filter(status__in=[DeviceCommand.Status.PENDING, DeviceCommand.Status.SENT]).order_by("created_at").first()
    if not command:
        return HttpResponse("OK", content_type="text/plain")
    command.status = DeviceCommand.Status.SENT
    command.sent_at = timezone.now()
    command.attempts += 1
    command.save(update_fields=["status", "sent_at", "attempts", "updated_at"])
    return HttpResponse(f"C:{command.pk}:{command.command}", content_type="text/plain")


@extend_schema(request=OpenApiTypes.BYTE, responses=OpenApiTypes.STR)
@api_view(["POST"])
@permission_classes([AllowAny])
def iclock_devicecmd(request):
    device = _device_for_request(request)
    if not device:
        return HttpResponse("ERROR: unknown device", status=403, content_type="text/plain")
    _touch_device(device, request)
    body = request.body.decode("utf-8", errors="replace")
    command_id_match = re.search(r"(?:^|[&\s])ID=(\d+)", body, re.IGNORECASE)
    return_match = re.search(r"(?:^|[&\s])Return=(-?\d+)", body, re.IGNORECASE)
    if command_id_match:
        command = device.commands.filter(pk=int(command_id_match.group(1))).first()
        if command:
            return_code = int(return_match.group(1)) if return_match else -1
            command.status = DeviceCommand.Status.ACKNOWLEDGED if return_code == 0 else DeviceCommand.Status.FAILED
            command.acknowledged_at = timezone.now()
            command.response = body[:2000]
            command.save(update_fields=["status", "acknowledged_at", "response", "updated_at"])
    return HttpResponse("OK", content_type="text/plain")


class DeviceViewSet(AuditedModelViewSet):
    queryset = AttendanceDevice.objects.select_related("branch", "branch__empresa").annotate(last_marking=Max("events__occurred_at")).order_by("name")
    serializer_class = DeviceSerializer
    permission_classes = [HasModulePermission]
    permission_module = "attendance.devices"
    scope_branch_lookup = "branch"
    filterset_fields = ["branch", "status"]
    search_fields = ["serial_number", "name", "device_model", "location"]

    @action(detail=True, methods=["post"], url_path="test-connection")
    def test_connection(self, request, pk=None):
        device = self.get_object()
        try:
            test_device_tcp_connection(device)
        except (OSError, ValueError) as exc:
            return Response({"reachable": False, "message": str(exc)})
        return Response({"reachable": True, "message": f"{device.ip_address}:{device.port} acepta conexiones TCP."})


class LocalEnrollmentCreateView(generics.CreateAPIView):
    serializer_class = LocalEnrollmentSerializer
    permission_classes = [HasModulePermission]
    permission_module = "attendance.enrollments"
    permission_action = "can_create"


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def local_network(request):
    addresses = local_ipv4_addresses()
    return Response({
        "addresses": addresses,
        "recommended_address": addresses[0] if addresses else None,
        "port": request.get_port(),
        "callback_path": "/iclock/cdata",
    })


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
