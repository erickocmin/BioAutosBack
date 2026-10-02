from datetime import datetime

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Empleado, Perfil, Usuario, UsuarioPerfil
from apps.attendance.models import AttendanceDevice, AttendanceEvent, DailyAttendance, DeviceCommand
from apps.attendance.services import parse_attlog_line, process_event


@pytest.fixture
def device(branch):
    return AttendanceDevice.objects.create(serial_number="ZK-001", name="Reloj principal", branch=branch)


def test_parse_attlog_preserves_raw_data():
    raw = "1001\t2026-09-20 08:00:00\t0\t1"
    data = parse_attlog_line(raw)
    assert data["biometric_pin"] == "1001"
    assert data["verification_method"] == "fingerprint"
    assert data["direction"] == "entry"
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
def test_attlog_processes_entry_and_exit_immediately(user, device):
    client = APIClient()
    body = "\n".join([
        "1001\t2026-09-20 08:00:00\t0\t1",
        "1001\t2026-09-20 17:00:00\t1\t1",
    ])
    assert client.post("/iclock/cdata?SN=ZK-001&table=ATTLOG", body, content_type="text/plain").status_code == 200
    daily = DailyAttendance.objects.get(employee=user.empleado, date="2026-09-20")
    assert daily.worked_minutes == 540
    assert list(AttendanceEvent.objects.order_by("occurred_at").values_list("direction", flat=True)) == ["entry", "exit"]


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


@pytest.mark.django_db
def test_local_enrollment_creates_login_employee_and_device_command(api_client, branch, device):
    profile = Perfil.objects.create(codigo="operator", nombre="Operador")
    response = api_client.post("/api/v1/attendance/enrollments/", {
        "username": "operador",
        "email": "operador@example.test",
        "temporary_password": "Temporary.2026",
        "first_name": "Luis",
        "last_name": "Prueba",
        "branch": branch.pk,
        "employee_code": "E002",
        "document_number": "87654321",
        "job_title": "Operador",
        "biometric_pin": "1002",
        "device": device.pk,
        "profile": profile.pk,
    }, format="json")
    assert response.status_code == 201
    employee = Empleado.objects.get(codigo="E002")
    assert employee.usuario == Usuario.objects.get(username="operador")
    assert UsuarioPerfil.objects.filter(user=employee.usuario, profile=profile, branch=branch).exists()
    command = DeviceCommand.objects.get()
    assert "PIN=1002" in command.command
    assert "Temporary.2026" not in command.command

    poll = APIClient().get("/iclock/getrequest?SN=ZK-001")
    assert poll.status_code == 200
    assert f"C:{command.pk}:DATA UPDATE USERINFO" in poll.content.decode()
    acknowledged = APIClient().post(
        "/iclock/devicecmd?SN=ZK-001",
        f"ID={command.pk}&Return=0&CMD=DATA",
        content_type="text/plain",
    )
    assert acknowledged.status_code == 200
    command.refresh_from_db()
    assert command.status == DeviceCommand.Status.ACKNOWLEDGED


@pytest.mark.django_db
def test_enrollment_links_and_processes_previous_unknown_pin(api_client, branch, device):
    event = AttendanceEvent.objects.create(
        device=device,
        biometric_pin="1999",
        occurred_at=timezone.make_aware(datetime(2026, 9, 21, 8)),
        direction=AttendanceEvent.Direction.ENTRY,
        verification_method=AttendanceEvent.VerificationMethod.FINGERPRINT,
        raw_data="unknown",
    )
    response = api_client.post("/api/v1/attendance/enrollments/", {
        "username": "previous-pin",
        "email": "previous-pin@example.test",
        "temporary_password": "Temporary.2026",
        "first_name": "PIN",
        "last_name": "Anterior",
        "branch": branch.pk,
        "employee_code": "E003",
        "document_number": "87654322",
        "biometric_pin": "1999",
    }, format="json")
    assert response.status_code == 201
    event.refresh_from_db()
    assert event.employee == Empleado.objects.get(codigo="E003")
    assert event.processed_at is not None
    assert DailyAttendance.objects.filter(employee=event.employee, date="2026-09-21").exists()
