from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import DailyAttendanceViewSet, DeviceViewSet, EventViewSet, LocalEnrollmentCreateView, iclock_cdata, local_network

router = SimpleRouter()
router.register("devices", DeviceViewSet)
router.register("events", EventViewSet)
router.register("daily", DailyAttendanceViewSet)

urlpatterns = [
    path("iclock/cdata", iclock_cdata, name="iclock-cdata"),
    path("enrollments/", LocalEnrollmentCreateView.as_view(), name="local-enrollment"),
    path("local-network/", local_network, name="local-network"),
    *router.urls,
]
