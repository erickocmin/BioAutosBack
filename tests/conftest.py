import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Empleado, Usuario
from apps.core.models import Empresa, Sucursal


@pytest.fixture
def company(db):
    return Empresa.objects.create(ruc="20123456789", razon_social="Empresa Demo SAC")


@pytest.fixture
def branch(company):
    return Sucursal.objects.create(empresa=company, codigo="LIM", nombre="Lima")


@pytest.fixture
def user(db, branch):
    user = Usuario.objects.create_user(username="admin", email="admin@example.test", password="SafePassword.123", is_superuser=True)
    Empleado.objects.create(usuario=user, sucursal=branch, codigo="E001", numero_documento="12345678", nombres="Ana", apellidos="Demo", biometric_pin="1001")
    return user


@pytest.fixture
def api_client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client
