from django.core.management.base import BaseCommand

from apps.accounts.models import Empleado, Modulo, Perfil, Permiso, Usuario, UsuarioPerfil
from apps.attendance.models import AttendanceDevice
from apps.core.models import Empresa, Sucursal
from apps.inventory.models import Almacen, Marca, Producto, Proveedor, UnidadMedida
from apps.treasury.models import Caja, FormaPago


MODULES = [
    "core.empresas", "core.sucursales", "core.oficinas", "core.ubigeo", "core.tipos_documento", "core.series_documento",
    "accounts.usuarios", "accounts.empleados", "accounts.perfiles", "accounts.modulos", "accounts.permisos",
    "inventory.almacenes", "inventory.unidades_medida", "inventory.marcas", "inventory.proveedores", "inventory.productos", "inventory.kardex", "inventory.movimientos",
    "treasury.cajas", "treasury.formas_pago", "treasury.arqueos", "treasury.cierres_diarios",
    "attendance.devices", "attendance.events", "attendance.daily",
]


class Command(BaseCommand):
    help = "Crea datos ficticios mínimos; nunca usa PII ni secretos reales."

    def handle(self, *args, **options):
        company, _ = Empresa.objects.get_or_create(ruc="20000000001", defaults={"razon_social": "Transporte Demo SAC", "nombre_comercial": "Demo"})
        branch, _ = Sucursal.objects.get_or_create(empresa=company, codigo="DEMO", defaults={"nombre": "Sucursal Demo", "direccion": "Dirección ficticia 123"})
        profile, _ = Perfil.objects.get_or_create(codigo="demo-admin", defaults={"nombre": "Administrador demo"})
        for code in MODULES:
            module, _ = Modulo.objects.get_or_create(code=code, defaults={"name": code.replace("_", " ").title()})
            Permiso.objects.update_or_create(profile=profile, module=module, defaults={
                "can_view": True, "can_create": True, "can_update": True, "can_delete": True,
                "can_approve": True, "can_cancel": True, "can_close": True, "can_export": True,
            })
        user, created = Usuario.objects.get_or_create(username="demo", defaults={"email": "demo@example.test", "first_name": "Usuario", "last_name": "Demo"})
        if created:
            user.set_password("DemoOnly.2026")
            user.save(update_fields=["password"])
        UsuarioPerfil.objects.get_or_create(user=user, profile=profile, company=company, branch=branch)
        Empleado.objects.get_or_create(codigo="EMP-DEMO", defaults={"usuario": user, "sucursal": branch, "numero_documento": "00000001", "nombres": "Persona", "apellidos": "Demo", "biometric_pin": "1001"})
        unit, _ = UnidadMedida.objects.get_or_create(codigo="UND", defaults={"nombre": "Unidad", "factor_base": 1})
        brand, _ = Marca.objects.get_or_create(nombre="Marca Demo")
        Producto.objects.get_or_create(codigo="PROD-DEMO", defaults={"nombre": "Producto demostrativo", "marca": brand, "unidad_base": unit})
        Almacen.objects.get_or_create(sucursal=branch, codigo="ALM-DEMO", defaults={"nombre": "Almacén Demo"})
        Almacen.objects.get_or_create(sucursal=branch, codigo="ALM-DEMO-2", defaults={"nombre": "Almacén Secundario Demo"})
        Proveedor.objects.get_or_create(ruc="20999999991", defaults={"razon_social": "Proveedor Demo SAC"})
        Caja.objects.get_or_create(sucursal=branch, codigo="CAJA-DEMO", defaults={"nombre": "Caja Demo"})
        FormaPago.objects.get_or_create(codigo="EFE", defaults={"nombre": "Efectivo", "es_efectivo": True})
        AttendanceDevice.objects.get_or_create(serial_number="ZK-DEMO-001", defaults={"name": "Reloj Demo", "branch": branch, "device_model": "ZKTeco Demo"})
        self.stdout.write(self.style.SUCCESS("Datos demo creados. Usuario: demo / DemoOnly.2026"))
