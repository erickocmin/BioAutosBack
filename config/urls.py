from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.attendance.views import iclock_cdata, iclock_devicecmd, iclock_getrequest

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/core/", include("apps.core.urls")),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/treasury/", include("apps.treasury.urls")),
    path("api/v1/attendance/", include("apps.attendance.urls")),
    path("iclock/cdata", iclock_cdata, name="iclock-cdata-root"),
    path("iclock/cdata.aspx", iclock_cdata, name="iclock-cdata-aspx-root"),
    path("iclock/getrequest", iclock_getrequest, name="iclock-getrequest-root"),
    path("iclock/getrequest.aspx", iclock_getrequest, name="iclock-getrequest-aspx-root"),
    path("iclock/devicecmd", iclock_devicecmd, name="iclock-devicecmd-root"),
    path("iclock/devicecmd.aspx", iclock_devicecmd, name="iclock-devicecmd-aspx-root"),
]
