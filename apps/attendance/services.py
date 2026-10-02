import logging
import ipaddress
import socket
from datetime import datetime, time, timedelta

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import Empleado
from .models import AttendanceEvent, DailyAttendance

logger = logging.getLogger("sisgetran.attendance")

VERIFY_MAP = {
    "0": AttendanceEvent.VerificationMethod.PASSWORD,
    "1": AttendanceEvent.VerificationMethod.FINGERPRINT,
    "2": AttendanceEvent.VerificationMethod.CARD,
    "3": AttendanceEvent.VerificationMethod.PASSWORD,
    "4": AttendanceEvent.VerificationMethod.CARD,
    "15": AttendanceEvent.VerificationMethod.FACE,
    "20": AttendanceEvent.VerificationMethod.FACE,
}

STATUS_DIRECTION_MAP = {
    "0": AttendanceEvent.Direction.ENTRY,
    "1": AttendanceEvent.Direction.EXIT,
    "2": AttendanceEvent.Direction.EXIT,
    "3": AttendanceEvent.Direction.ENTRY,
    "4": AttendanceEvent.Direction.ENTRY,
    "5": AttendanceEvent.Direction.EXIT,
}


def parse_attlog_line(line):
    parts = line.strip().split("\t")
    if len(parts) < 2:
        parts = line.strip().split()
        if len(parts) >= 3:
            parts = [parts[0], f"{parts[1]} {parts[2]}", *parts[3:]]
    if len(parts) < 2:
        raise ValueError("Línea ATTLOG inválida")
    timestamp = datetime.strptime(parts[1], "%Y-%m-%d %H:%M:%S")
    if timezone.is_naive(timestamp):
        timestamp = timezone.make_aware(timestamp, timezone.get_current_timezone())
    device_status = parts[2] if len(parts) > 2 else ""
    return {
        "biometric_pin": parts[0],
        "occurred_at": timestamp,
        "device_status": device_status,
        "direction": STATUS_DIRECTION_MAP.get(device_status, AttendanceEvent.Direction.UNKNOWN),
        "verification_method": VERIFY_MAP.get(parts[3] if len(parts) > 3 else "", AttendanceEvent.VerificationMethod.OTHER),
        "raw_data": line,
    }


@transaction.atomic
def receive_attlog(*, device, raw_body):
    created_events = []
    duplicate_count = 0
    for line in raw_body.splitlines():
        line = line.strip()
        if not line or line.upper().startswith("ATTLOG"):
            continue
        data = parse_attlog_line(line)
        employee = Empleado.objects.filter(biometric_pin=data["biometric_pin"], activo=True).first()
        event, created = AttendanceEvent.objects.get_or_create(
            device=device,
            biometric_pin=data["biometric_pin"],
            occurred_at=data["occurred_at"],
            verification_method=data["verification_method"],
            defaults={
                "employee": employee,
                "device_status": data["device_status"],
                "direction": data["direction"],
                "raw_data": data["raw_data"],
            },
        )
        if created:
            created_events.append(event)
        else:
            duplicate_count += 1
    return created_events, duplicate_count


def is_private_client_ip(value):
    try:
        address = ipaddress.ip_address(value)
    except ValueError:
        return False
    return address.is_private or address.is_loopback or address.is_link_local


def local_ipv4_addresses():
    addresses = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            addresses.append(probe.getsockname()[0])
    except OSError:
        pass
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.append(item[4][0])
    except OSError:
        pass
    valid = [address for address in addresses if is_private_client_ip(address) and not ipaddress.ip_address(address).is_loopback]
    return list(dict.fromkeys(valid))


def test_device_tcp_connection(device, timeout=1.5):
    if not device.ip_address:
        raise ValueError("Configura primero la IP local del huellero.")
    if not is_private_client_ip(device.ip_address):
        raise ValueError("Por seguridad, la prueba solo permite direcciones de red privada.")
    with socket.create_connection((device.ip_address, device.port), timeout=timeout):
        return True


@transaction.atomic
def process_event(event):
    if not event.employee_id:
        return None
    event = AttendanceEvent.objects.select_for_update().get(pk=event.pk)
    day = timezone.localtime(event.occurred_at).date()
    day_start = timezone.make_aware(datetime.combine(day, time.min), timezone.get_current_timezone())
    events = AttendanceEvent.objects.filter(
        employee=event.employee, occurred_at__gte=day_start, occurred_at__lt=day_start + timedelta(days=1)
    ).order_by("occurred_at")
    first = events.filter(direction=AttendanceEvent.Direction.ENTRY).first() or events.first()
    last = events.filter(direction=AttendanceEvent.Direction.EXIT).last()
    if not last:
        candidate = events.last()
        last = candidate if candidate and first and candidate.pk != first.pk else None
    worked_minutes = max(0, int((last.occurred_at - first.occurred_at).total_seconds() // 60)) if first and last and first.pk != last.pk else 0
    daily, _ = DailyAttendance.objects.update_or_create(
        employee=event.employee,
        date=day,
        defaults={
            "first_entry": first.occurred_at if first else None,
            "last_exit": last.occurred_at if last and first and last.pk != first.pk else None,
            "worked_minutes": worked_minutes,
            "status": "calculated",
        },
    )
    event.processed_at = timezone.now()
    event.save(update_fields=["processed_at"])
    return daily
