from datetime import datetime, time, timedelta

from django_filters import rest_framework as filters
from django.utils import timezone

from .models import AttendanceEvent, DailyAttendance


class EventFilter(filters.FilterSet):
    date_from = filters.DateFilter(method="filter_date_from")
    date_to = filters.DateFilter(method="filter_date_to")
    branch = filters.NumberFilter(field_name="device__branch_id")
    processed = filters.BooleanFilter(method="filter_processed")

    class Meta:
        model = AttendanceEvent
        fields = ("device", "employee", "biometric_pin", "verification_method", "direction", "branch")

    def filter_processed(self, queryset, _name, value):
        return queryset.filter(processed_at__isnull=not value)

    def filter_date_from(self, queryset, _name, value):
        start = timezone.make_aware(datetime.combine(value, time.min), timezone.get_current_timezone())
        return queryset.filter(occurred_at__gte=start)

    def filter_date_to(self, queryset, _name, value):
        end = timezone.make_aware(datetime.combine(value, time.min), timezone.get_current_timezone()) + timedelta(days=1)
        return queryset.filter(occurred_at__lt=end)


class DailyAttendanceFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_to = filters.DateFilter(field_name="date", lookup_expr="lte")
    branch = filters.NumberFilter(field_name="employee__sucursal_id")

    class Meta:
        model = DailyAttendance
        fields = ("employee", "date", "status", "branch")
