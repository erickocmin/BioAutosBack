import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Modulo, Perfil, Permiso, Usuario, UsuarioPerfil
from apps.treasury.models import Arqueo, Caja


@pytest.mark.django_db
def test_login_refresh_logout_and_blacklist(user):
    client = APIClient()
    login = client.post("/api/v1/accounts/auth/login/", {"usuario": "admin", "password": "SafePassword.123"}, format="json")
    assert login.status_code == 200
    refresh = login.json()["refresh"]
    rotated = client.post("/api/v1/accounts/auth/refresh/", {"refresh": refresh}, format="json")
    assert rotated.status_code == 200
    refresh = rotated.json()["refresh"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
    assert client.post("/api/v1/accounts/auth/logout/", {"refresh": refresh}, format="json").status_code == 205
    assert client.post("/api/v1/accounts/auth/refresh/", {"refresh": refresh}, format="json").status_code == 401


@pytest.mark.django_db
def test_custom_close_action_requires_close_permission(company, branch, user):
    cashbox = Caja.objects.create(sucursal=branch, codigo="C1", nombre="Caja")
    cash_count = Arqueo.objects.create(sucursal=branch, caja=cashbox, cajero=user, fecha=timezone.localdate())
    regular = Usuario.objects.create_user("cashier", "cashier@example.test", "SafePassword.123")
    module = Modulo.objects.create(code="treasury.arqueos", name="Arqueos")
    profile = Perfil.objects.create(codigo="cash-view", nombre="Consulta de caja")
    Permiso.objects.create(profile=profile, module=module, can_view=True, can_update=True, can_close=False)
    UsuarioPerfil.objects.create(user=regular, profile=profile, company=company, branch=branch)
    client = APIClient()
    client.force_authenticate(regular)
    assert client.post(f"/api/v1/treasury/arqueos/{cash_count.pk}/cerrar/").status_code == 403
