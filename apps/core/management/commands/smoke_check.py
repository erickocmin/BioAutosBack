from django.core.management.base import BaseCommand, CommandError
from rest_framework.test import APIClient

from apps.attendance.models import AttendanceEvent


class Command(BaseCommand):
    help = "Ejecuta un smoke test integrado sobre datos demo sin servicios externos."

    def handle(self, *args, **options):
        client = APIClient(HTTP_HOST="localhost")
        login = client.post("/api/v1/accounts/auth/login/", {"usuario": "demo", "password": "DemoOnly.2026"}, format="json")
        if login.status_code != 200:
            raise CommandError(f"Login falló: {login.status_code}")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        checks = {
            "me": client.get("/api/v1/accounts/auth/me/"),
            "products": client.get("/api/v1/inventory/productos/?page=1&page_size=20&search=Demo"),
            "cash": client.get("/api/v1/treasury/arqueos/?page=1&page_size=20"),
        }
        for name, response in checks.items():
            if response.status_code != 200:
                raise CommandError(f"{name} falló: {response.status_code}")
        device = APIClient(HTTP_HOST="localhost")
        handshake = device.get("/iclock/cdata?SN=ZK-DEMO-001")
        body = "1001\t2026-09-20 08:00:00\t0\t1"
        before = AttendanceEvent.objects.count()
        first = device.post("/iclock/cdata?SN=ZK-DEMO-001", body, content_type="text/plain")
        second = device.post("/iclock/cdata?SN=ZK-DEMO-001", body, content_type="text/plain")
        after = AttendanceEvent.objects.count()
        if handshake.status_code != 200 or first.status_code != 200 or second.status_code != 200 or after - before > 1:
            raise CommandError("Smoke ZKTeco falló")
        self.stdout.write(self.style.SUCCESS(
            f"OK login={login.data['usuario']['username']} products={checks['products'].data['count']} "
            f"handshake=200 attlog={first.content.decode()} duplicate={second.content.decode()}"
        ))
