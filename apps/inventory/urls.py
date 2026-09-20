from rest_framework.routers import SimpleRouter

from .views import AlmacenViewSet, KardexViewSet, MarcaViewSet, MovementViewSet, ProductoViewSet, ProveedorViewSet, UnidadMedidaViewSet

router = SimpleRouter()
router.register("almacenes", AlmacenViewSet)
router.register("unidades-medida", UnidadMedidaViewSet)
router.register("marcas", MarcaViewSet)
router.register("proveedores", ProveedorViewSet)
router.register("productos", ProductoViewSet)
router.register("kardex", KardexViewSet)
router.register("movimientos", MovementViewSet)

urlpatterns = router.urls
