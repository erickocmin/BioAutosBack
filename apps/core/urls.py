from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import EmpresaViewSet, OficinaViewSet, SerieDocumentoViewSet, SucursalViewSet, TipoDocumentoViewSet, UbigeoViewSet, menu

router = SimpleRouter()
router.register("empresas", EmpresaViewSet)
router.register("sucursales", SucursalViewSet)
router.register("oficinas", OficinaViewSet)
router.register("ubigeos", UbigeoViewSet)
router.register("tipos-documento", TipoDocumentoViewSet)
router.register("series-documento", SerieDocumentoViewSet)

urlpatterns = [path("menu/", menu, name="menu"), *router.urls]
