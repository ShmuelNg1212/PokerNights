"""The audit log's only write path."""

from .models import AuditEvent


def record(action, *, actor=None, group_id=None, session_id=None, target=None, summary="", reason="", data=None):
    """Write one event. Call it inside the caller's transaction so both roll back together."""
    return AuditEvent.objects.create(
        action=action,
        actor=actor,
        group_id=group_id,
        session_id=session_id,
        target_type=target._meta.label_lower if target is not None else "",
        target_id=target.pk if target is not None else None,
        summary=summary[:255],
        reason=reason[:255],
        data=data or {},
    )
