import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from rest_framework_simplejwt.tokens import AccessToken


class Command(BaseCommand):
    help = "Mide consultas, tiempo y payload de endpoints representativos con un usuario existente."

    def add_arguments(self, parser):
        parser.add_argument("--username", required=True)

    def handle(self, *args, **options):
        try:
            user = get_user_model().objects.get(username=options["username"])
        except get_user_model().DoesNotExist as exc:
            raise CommandError("El usuario indicado no existe.") from exc
        client = Client(HTTP_HOST="localhost")
        client.defaults["HTTP_AUTHORIZATION"] = f"Bearer {AccessToken.for_user(user)}"
        paths = (
            "/api/v1/core/empresas/", "/api/v1/accounts/empleados/",
            "/api/v1/inventory/productos/", "/api/v1/inventory/movimientos/",
            "/api/v1/treasury/arqueos/", "/api/v1/attendance/events/",
            "/api/v1/attendance/devices/",
        )
        self.stdout.write(f"database={connection.vendor} version={getattr(connection, 'mysql_version', 'n/a')}")
        for path in paths:
            started = time.perf_counter()
            with CaptureQueriesContext(connection) as captured:
                response = client.get(path)
            elapsed_ms = (time.perf_counter() - started) * 1000
            records = response.data.get("count", 0) if hasattr(response, "data") and isinstance(response.data, dict) else 0
            self.stdout.write(
                f"{path} status={response.status_code} records={records} queries={len(captured)} "
                f"time_ms={elapsed_ms:.2f} bytes={len(response.content)}"
            )
