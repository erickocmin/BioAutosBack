from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DailyAttendanceViewSet, DeviceViewSet, EventViewSet, iclock_cdata

router = SimpleRouter()
router.register("devices", DeviceViewSet)
router.register("events", EventViewSet)
router.register("daily", DailyAttendanceViewSet)

urlpatterns = [path("iclock/cdata", iclock_cdata, name="iclock-cdata"), *router.urls]
