from django.core.management.base import BaseCommand

from apps.attendance.models import AttendanceEvent
from apps.attendance.services import process_event


class Command(BaseCommand):
    help = "Procesa eventos de asistencia pendientes de forma idempotente."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=1000)

    def handle(self, *args, **options):
        events = AttendanceEvent.objects.filter(processed_at__isnull=True, employee__isnull=False).order_by("received_at")[:options["limit"]]
        processed = 0
        for event in events:
            process_event(event)
            processed += 1
        self.stdout.write(self.style.SUCCESS(f"{processed} eventos procesados"))
