from .models import AuditEntry


def record(actor, action, obj, summary, reason=""):
    return AuditEntry.objects.create(
        actor=actor if getattr(actor, "pk", None) else None, action=action,
        object_type=obj.__class__.__name__ if obj is not None else "", object_id=str(getattr(obj, "pk", "") or ""),
        summary=summary[:300], reason=reason or "",
    )
