from datetime import datetime

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.attendance.models import AttendanceDevice, AttendanceEvent, DailyAttendance
from apps.attendance.services import parse_attlog_line, process_event


@pytest.fixture
def device(branch):
    return AttendanceDevice.objects.create(serial_number="ZK-001", name="Reloj principal", branch=branch)


def test_parse_attlog_preserves_raw_data():
    raw = "1001\t2026-09-20 08:00:00\t0\t1"
    data = parse_attlog_line(raw)
    assert data["biometric_pin"] == "1001"
    assert data["verification_method"] == "fingerprint"
    assert data["raw_data"] == raw


@pytest.mark.django_db
def test_unknown_device_is_rejected():
    response = APIClient().get("/iclock/cdata?SN=UNKNOWN")
    assert response.status_code == 403


@pytest.mark.django_db
def test_device_handshake(device):
    response = APIClient().get("/iclock/cdata?SN=ZK-001")
    assert response.status_code == 200
    assert b"TransInterval" in response.content


@pytest.mark.django_db
def test_attlog_is_idempotent(device):
    body = "1001\t2026-09-20 08:00:00\t0\t1"
    client = APIClient()
    assert client.post("/iclock/cdata?SN=ZK-001", body, content_type="text/plain").status_code == 200
    assert client.post("/iclock/cdata?SN=ZK-001", body, content_type="text/plain").status_code == 200
    assert AttendanceEvent.objects.count() == 1
    assert AttendanceEvent.objects.get().raw_data == body


@pytest.mark.django_db
def test_unknown_pin_is_stored_for_reprocessing(device):
    APIClient().post("/iclock/cdata?SN=ZK-001", "9999\t2026-09-20 08:00:00\t0\t15", content_type="text/plain")
    event = AttendanceEvent.objects.get()
    assert event.employee is None
    assert event.verification_method == "face"


@pytest.mark.django_db
def test_daily_attendance_is_derived_from_events(user, device):
    employee = user.empleado
    first = AttendanceEvent.objects.create(device=device, employee=employee, biometric_pin="1001", occurred_at=timezone.make_aware(datetime(2026, 9, 20, 8)), verification_method="fingerprint", raw_data="first")
    AttendanceEvent.objects.create(device=device, employee=employee, biometric_pin="1001", occurred_at=timezone.make_aware(datetime(2026, 9, 20, 17)), verification_method="fingerprint", raw_data="last")
    process_event(first)
    daily = DailyAttendance.objects.get(employee=employee, date="2026-09-20")
    assert daily.worked_minutes == 540
    assert timezone.localtime(daily.first_entry).hour == 8
    assert timezone.localtime(daily.last_exit).hour == 17


@pytest.mark.django_db
def test_attendance_event_is_immutable(user, device):
    event = AttendanceEvent.objects.create(device=device, employee=user.empleado, biometric_pin="1001", occurred_at=timezone.now(), raw_data="raw")
    with pytest.raises(TypeError):
        event.delete()


@pytest.mark.django_db
def test_event_list_hides_raw_data_but_detail_keeps_it(api_client, user, device):
    event = AttendanceEvent.objects.create(device=device, employee=user.empleado, biometric_pin="1001", occurred_at=timezone.now(), raw_data="sensitive-device-line")
    listed = api_client.get("/api/v1/attendance/events/")
    detail = api_client.get(f"/api/v1/attendance/events/{event.pk}/")
    assert listed.status_code == detail.status_code == 200
    assert "raw_data" not in listed.json()["results"][0]
    assert detail.json()["raw_data"] == "sensitive-device-line"
