from rest_framework import viewsets

from common.services import audit
from common.scoping import ScopedQuerysetMixin


class AuditedModelViewSet(ScopedQuerysetMixin, viewsets.ModelViewSet):
    def perform_create(self, serializer):
        instance = serializer.save()
        audit(actor=self.request.user, action="create", instance=instance, request=self.request)

    def perform_update(self, serializer):
        instance = serializer.save()
        audit(actor=self.request.user, action="update", instance=instance, request=self.request)

    def perform_destroy(self, instance):
        audit(actor=self.request.user, action="delete", instance=instance, request=self.request)
        for field_name in ("activo", "activa", "is_active"):
            if hasattr(instance, field_name):
                setattr(instance, field_name, False)
                instance.save(update_fields=[field_name, "updated_at"] if hasattr(instance, "updated_at") else [field_name])
                return
        instance.delete()
