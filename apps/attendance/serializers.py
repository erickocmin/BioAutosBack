from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import AttendanceDevice, AttendanceEvent, DailyAttendance


class DeviceSerializer(serializers.ModelSerializer):
    last_marking = serializers.DateTimeField(read_only=True)
    connection_state = serializers.SerializerMethodField()

    class Meta:
        model = AttendanceDevice
        fields = "__all__"

    def get_connection_state(self, obj) -> str:
        reference = max(filter(None, (obj.last_connection, getattr(obj, "last_marking", None))), default=None)
        if not reference:
            return "never_connected"
        return "recent" if reference >= timezone.now() - timedelta(minutes=10) else "disconnected"


class EventSerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source="employee.__str__", read_only=True)

    class Meta:
        model = AttendanceEvent
        fields = "__all__"
        read_only_fields = ("id", "device", "employee", "biometric_pin", "occurred_at", "device_status", "verification_method", "source_event_id", "confidence", "raw_data", "received_at", "processed_at")


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
