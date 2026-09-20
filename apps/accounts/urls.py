from django.urls import path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import EmpleadoViewSet, ModuloViewSet, PerfilViewSet, PermisoViewSet, UsuarioViewSet, login, logout, me

router = SimpleRouter()
router.register("usuarios", UsuarioViewSet)
router.register("empleados", EmpleadoViewSet)
router.register("perfiles", PerfilViewSet)
router.register("modulos", ModuloViewSet)
router.register("permisos", PermisoViewSet)

urlpatterns = [
    path("auth/login/", login, name="login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/logout/", logout, name="logout"),
    path("auth/me/", me, name="me"),
    *router.urls,
]
