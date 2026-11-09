from ..models.models import ContestAuditLog

def log_contest_audit(contest, actor, action, target_type='', target_id='', details='', ip='127.0.0.1'):
    """Log an administrative action for the contest."""
    try:
        return ContestAuditLog.objects.create(
            contest=contest,
            actor=actor,
            action=action,
            target_type=target_type,
            target_id=str(target_id),
            details=details,
            ip_address=ip
        )
    except Exception as e:
        print(f"[Audit Log Error] {e}")
        return None
