from datetime import timedelta

from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from rest_framework import serializers

from apps.accounts.models import Empleado, Perfil, Usuario, UsuarioPerfil
from apps.core.models import Sucursal
from .models import AttendanceDevice, AttendanceEvent, DailyAttendance, DeviceCommand


class DeviceSerializer(serializers.ModelSerializer):
    last_marking = serializers.DateTimeField(read_only=True)
    connection_state = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceDevice
        fields = "__all__"
        read_only_fields = ("last_connection", "created_at", "updated_at")

    def get_connection_state(self, obj) -> str:
        reference = max(filter(None, (obj.last_connection, getattr(obj, "last_marking", None))), default=None)
        if not reference:
            return "never_connected"
        return "recent" if reference >= timezone.now() - timedelta(minutes=10) else "disconnected"


class EventSerializer(serializers.ModelSerializer):
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceEvent
        fields = "__all__"
        read_only_fields = ("id", "device", "employee", "biometric_pin", "occurred_at", "device_status", "verification_method", "source_event_id", "confidence", "raw_data", "received_at", "processed_at")

    def get_employee_name(self, obj) -> str | None:
        return str(obj.employee) if obj.employee_id else None


class EventListSerializer(EventSerializer):
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop("raw_data", None)
        return data


class DailyAttendanceSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.__str__", read_only=True)

    class Meta:
        model = DailyAttendance
        fields = "__all__"
        read_only_fields = ("id", "employee", "date", "first_entry", "last_exit", "worked_minutes", "late_minutes", "overtime_minutes", "status", "created_at", "updated_at")


class LocalEnrollmentSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    temporary_password = serializers.CharField(write_only=True, validators=[validate_password])
    first_name = serializers.CharField(max_length=100)
    last_name = serializers.CharField(max_length=120)
    branch = serializers.PrimaryKeyRelatedField(queryset=Sucursal.objects.filter(activa=True))
    employee_code = serializers.CharField(max_length=30)
    document_number = serializers.RegexField(r"^[0-9]{8,11}$")
    job_title = serializers.CharField(max_length=100, allow_blank=True, required=False)
    biometric_pin = serializers.RegexField(r"^[0-9]{1,32}$")
    device = serializers.PrimaryKeyRelatedField(queryset=AttendanceDevice.objects.filter(status=AttendanceDevice.Status.ACTIVE), required=False, allow_null=True)
    profile = serializers.PrimaryKeyRelatedField(queryset=Perfil.objects.filter(is_active=True), required=False, allow_null=True)

    def validate(self, attrs):
        checks = (
            (Usuario.objects.filter(username=attrs["username"]).exists(), "username", "El usuario ya existe."),
            (Usuario.objects.filter(email=attrs["email"]).exists(), "email", "El correo ya existe."),
            (Empleado.objects.filter(codigo=attrs["employee_code"]).exists(), "employee_code", "El código ya existe."),
            (Empleado.objects.filter(biometric_pin=attrs["biometric_pin"]).exists(), "biometric_pin", "El PIN biométrico ya está asignado."),
        )
        errors = {field: message for exists, field, message in checks if exists}
        if attrs.get("device") and attrs["device"].branch_id != attrs["branch"].pk:
            errors["device"] = "El huellero debe pertenecer a la misma sucursal."
        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        device = validated_data.pop("device", None)
        profile = validated_data.pop("profile", None)
        password = validated_data.pop("temporary_password")
        branch = validated_data.pop("branch")
        user = Usuario(
            username=validated_data.pop("username"),
            email=validated_data.pop("email"),
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            must_change_password=True,
        )
        user.set_password(password)
        user.save()
        employee = Empleado.objects.create(
            usuario=user,
            sucursal=branch,
            codigo=validated_data.pop("employee_code"),
            numero_documento=validated_data.pop("document_number"),
            nombres=validated_data.pop("first_name"),
            apellidos=validated_data.pop("last_name"),
            cargo=validated_data.pop("job_title", ""),
            biometric_pin=validated_data.pop("biometric_pin"),
        )
        unmatched_events = list(AttendanceEvent.objects.filter(biometric_pin=employee.biometric_pin, employee__isnull=True))
        AttendanceEvent.objects.filter(pk__in=[event.pk for event in unmatched_events]).update(employee=employee)
        if unmatched_events:
            from .services import process_event

            for event in unmatched_events:
                event.employee = employee
                process_event(event)
        if profile:
            UsuarioPerfil.objects.create(user=user, profile=profile, company=branch.empresa, branch=branch)
        command = None
        if device:
            safe_name = " ".join(f"{employee.nombres} {employee.apellidos}".replace("\t", " ").replace("\n", " ").split())[:40]
            command = DeviceCommand.objects.create(
                device=device,
                command=f"DATA UPDATE USERINFO PIN={employee.biometric_pin}\tName={safe_name}\tPri=0\tPasswd=\tCard=\tGrp=1\tTZ=0000000100000000\tVerify=0",
            )
        return {"user": user, "employee": employee, "command": command}

    def to_representation(self, instance):
        return {
            "user_id": instance["user"].pk,
            "employee_id": instance["employee"].pk,
            "biometric_pin": instance["employee"].biometric_pin,
            "device_command_id": instance["command"].pk if instance["command"] else None,
            "next_step": "Registra la huella directamente en el equipo usando el mismo PIN biométrico.",
        }
