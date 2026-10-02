from django.db import models

from common.models import TimeStampedModel


class AttendanceDevice(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Activo"
        INACTIVE = "inactive", "Inactivo"
        MAINTENANCE = "maintenance", "Mantenimiento"

    serial_number = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    port = models.PositiveIntegerField(default=4370)
    device_model = models.CharField(max_length=100, blank=True)
    firmware = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=180, blank=True)
    branch = models.ForeignKey("core.Sucursal", related_name="attendance_devices", on_delete=models.PROTECT)
    last_connection = models.DateTimeField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)


class AttendanceEvent(models.Model):
    class Direction(models.TextChoices):
        ENTRY = "entry", "Entrada"
        EXIT = "exit", "Salida"
        UNKNOWN = "unknown", "Sin determinar"

    class VerificationMethod(models.TextChoices):
        FINGERPRINT = "fingerprint", "Huella"
        FACE = "face", "Rostro"
        CARD = "card", "Tarjeta"
        PASSWORD = "password", "Contraseña"
        OTHER = "other", "Otro"

    device = models.ForeignKey(AttendanceDevice, related_name="events", on_delete=models.PROTECT)
    employee = models.ForeignKey("accounts.Empleado", related_name="attendance_events", null=True, blank=True, on_delete=models.PROTECT)
    biometric_pin = models.CharField(max_length=32, db_index=True)
    occurred_at = models.DateTimeField(db_index=True)
    device_status = models.CharField(max_length=20, blank=True)
    direction = models.CharField(max_length=12, choices=Direction.choices, default=Direction.UNKNOWN, db_index=True)
    verification_method = models.CharField(max_length=20, choices=VerificationMethod.choices, default=VerificationMethod.OTHER)
    source_event_id = models.CharField(max_length=100, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=4, null=True, blank=True)
    raw_data = models.TextField()
    received_at = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["device", "biometric_pin", "occurred_at", "verification_method"],
            name="uq_attendance_event_idempotency",
        )]
        indexes = [models.Index(fields=["employee", "occurred_at"]), models.Index(fields=["device", "occurred_at"])]

    def delete(self, *args, **kwargs):
        raise TypeError("Los eventos de asistencia son inmutables.")


class DeviceCommand(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        SENT = "sent", "Enviado"
        ACKNOWLEDGED = "acknowledged", "Confirmado"
        FAILED = "failed", "Fallido"

    device = models.ForeignKey(AttendanceDevice, related_name="commands", on_delete=models.CASCADE)
    command = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    response = models.TextField(blank=True)

    class Meta:
        indexes = [models.Index(fields=["device", "status", "created_at"], name="att_cmd_dev_stat_created_idx")]


class DailyAttendance(TimeStampedModel):
    employee = models.ForeignKey("accounts.Empleado", related_name="daily_attendance", on_delete=models.PROTECT)
    date = models.DateField(db_index=True)
    first_entry = models.DateTimeField(null=True, blank=True)
    last_exit = models.DateTimeField(null=True, blank=True)
    worked_minutes = models.PositiveIntegerField(default=0)
    late_minutes = models.PositiveIntegerField(default=0)
    overtime_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=30, default="pending", db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["employee", "date"], name="uq_daily_attendance_employee_date")]
        indexes = [models.Index(fields=["date", "status"])]
