import logging
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
    "15": AttendanceEvent.VerificationMethod.FACE,
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
    return {
        "biometric_pin": parts[0],
        "occurred_at": timestamp,
        "device_status": parts[2] if len(parts) > 2 else "",
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
            defaults={"employee": employee, "device_status": data["device_status"], "raw_data": data["raw_data"]},
        )
        if created:
            created_events.append(event)
        else:
            duplicate_count += 1
    return created_events, duplicate_count


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
    first = events.first()
    last = events.last()
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
