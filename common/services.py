from .models import AuditLog


def audit(*, actor, action, instance, request=None, context=None):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "") if request else ""
    ip_address = forwarded.split(",")[0].strip() or (request.META.get("REMOTE_ADDR") if request else None)
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        entity=instance._meta.label,
        object_id=str(instance.pk),
        ip_address=ip_address,
        context=context or {},
    )
