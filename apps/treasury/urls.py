from rest_framework.routers import SimpleRouter

from .views import ArqueoViewSet, CajaViewSet, CierreDiarioViewSet, FormaPagoViewSet

router = SimpleRouter()
router.register("cajas", CajaViewSet)
router.register("formas-pago", FormaPagoViewSet)
router.register("arqueos", ArqueoViewSet)
router.register("cierres-diarios", CierreDiarioViewSet)

urlpatterns = router.urls
