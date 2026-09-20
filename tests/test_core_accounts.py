import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Empleado, Modulo, Perfil, Permiso, Usuario, UsuarioPerfil
from apps.core.models import Empresa, SerieDocumento, Sucursal, TipoDocumento


@pytest.mark.django_db
def test_password_is_hashed(user):
    assert user.password != "SafePassword.123"
    assert user.check_password("SafePassword.123")


@pytest.mark.django_db
def test_login_returns_tokens(user):
    response = APIClient().post("/api/v1/accounts/auth/login/", {"usuario": "admin", "password": "SafePassword.123"}, format="json")
    assert response.status_code == 200
    assert response.data["access"]
    assert response.data["refresh"]


@pytest.mark.django_db
def test_invalid_login_is_generic(user):
    response = APIClient().post("/api/v1/accounts/auth/login/", {"usuario": "admin", "password": "wrong"}, format="json")
    assert response.status_code == 401
    assert response.data["code"] == "authentication_failed"
    assert "admin" not in response.data["message"].lower()


@pytest.mark.django_db
def test_unauthenticated_request_is_blocked():
    assert APIClient().get("/api/v1/core/empresas/").status_code == 401


@pytest.mark.django_db
def test_permission_is_enforced_server_side(company, branch):
    regular = Usuario.objects.create_user("regular", "regular@example.test", "SafePassword.123")
    client = APIClient()
    client.force_authenticate(regular)
    assert client.get("/api/v1/core/empresas/").status_code == 403
    module = Modulo.objects.create(code="core.empresas", name="Empresas")
    profile = Perfil.objects.create(codigo="reader", nombre="Lector")
    Permiso.objects.create(profile=profile, module=module, can_view=True)
    UsuarioPerfil.objects.create(user=regular, profile=profile, company=company, branch=branch)
    assert client.get("/api/v1/core/empresas/").status_code == 200
    assert client.post("/api/v1/core/empresas/", {"ruc": "20999999999", "razon_social": "No"}).status_code == 403


@pytest.mark.django_db
def test_branch_scope_prevents_cross_company_idor(company, branch):
    other_company = Empresa.objects.create(ruc="20999999998", razon_social="Otra Empresa")
    other_branch = Sucursal.objects.create(empresa=other_company, codigo="OTH", nombre="Otra sucursal")
    regular = Usuario.objects.create_user("scoped", "scoped@example.test", "SafePassword.123")
    own_employee = Empleado.objects.create(usuario=regular, sucursal=branch, codigo="SCOPE-1", numero_documento="11111111", nombres="Usuario", apellidos="Local")
    other_employee = Empleado.objects.create(sucursal=other_branch, codigo="SCOPE-2", numero_documento="22222222", nombres="Usuario", apellidos="Externo")
    profile = Perfil.objects.create(codigo="branch-manager", nombre="Gestor de sucursal")
    for code in ("core.empresas", "accounts.empleados"):
        module = Modulo.objects.create(code=code, name=code)
        Permiso.objects.create(profile=profile, module=module, can_view=True, can_create=True)
    UsuarioPerfil.objects.create(user=regular, profile=profile, company=company, branch=branch)
    client = APIClient()
    client.force_authenticate(regular)
    companies = client.get("/api/v1/core/empresas/").data["results"]
    employees = client.get("/api/v1/accounts/empleados/").data["results"]
    assert [item["id"] for item in companies] == [company.pk]
    assert [item["id"] for item in employees] == [own_employee.pk]
    assert client.get(f"/api/v1/accounts/empleados/{other_employee.pk}/").status_code == 404
    assert client.post("/api/v1/accounts/empleados/", {
        "sucursal": other_branch.pk, "codigo": "FORBIDDEN", "numero_documento": "33333333",
        "nombres": "No", "apellidos": "Permitido",
    }, format="json").status_code == 403


@pytest.mark.django_db
def test_series_rollover_persists_next_series(company, branch):
    document_type = TipoDocumento.objects.create(codigo="01", nombre="Factura", codigo_sunat="01")
    series = SerieDocumento.objects.create(empresa=company, sucursal=branch, tipo_documento=document_type, serie="F001", valor_siguiente=2, valor_minimo=1, valor_maximo=2)
    issued = SerieDocumento.issue_next(series.pk)
    series.refresh_from_db()
    assert issued == ("F001", 2)
    assert (series.serie, series.valor_siguiente) == ("F002", 1)


@pytest.mark.django_db
def test_list_is_paginated(api_client):
    response = api_client.get("/api/v1/core/empresas/")
    assert response.status_code == 200
    assert set(response.data) >= {"count", "next", "previous", "results"}


@pytest.mark.django_db
def test_delete_is_a_soft_delete(api_client, company):
    response = api_client.delete(f"/api/v1/core/empresas/{company.pk}/")
    assert response.status_code == 204
    company.refresh_from_db()
    assert company.activa is False
