from django.utils import timezone
from backend.community.models import Report, ModerationAction, Post, Comment, Thread, ThreadPost

class ModerationService:
    @staticmethod
    def create_report(reporter, target_type, target_id, reason, details=""):
        return Report.objects.create(
            reporter=reporter,
            target_type=target_type,
            target_id=target_id,
            reason=reason,
            details=details
        )

    @staticmethod
    def get_pending_reports():
        return Report.objects.filter(status='pending').select_related('reporter__user')

    @staticmethod
    def apply_action(moderator, target_type, target_id, action, reason=""):
        # Record audit log
        ma = ModerationAction.objects.create(
            moderator=moderator,
            target_type=target_type,
            target_id=target_id,
            action=action,
            reason=reason
        )

        # Apply action to target
        if target_type == 'post':
            p = Post.objects.filter(id=target_id).first()
            if p:
                if action == 'hide': p.is_hidden = True
                elif action == 'restore': p.is_hidden = False
                elif action == 'pin': p.is_pinned = not p.is_pinned
                p.save()
        elif target_type == 'comment':
            c = Comment.objects.filter(id=target_id).first()
            if c:
                if action == 'hide': c.is_hidden = True
                elif action == 'restore': c.is_hidden = False
                c.save()
        elif target_type == 'thread':
            t = Thread.objects.filter(id=target_id).first()
            if t:
                if action == 'hide': t.is_hidden = True
                elif action == 'restore': t.is_hidden = False
                elif action == 'lock': t.is_locked = not t.is_locked
                elif action == 'pin': t.is_pinned = not t.is_pinned
                t.save()

        # Mark associated reports resolved
        Report.objects.filter(target_type=target_type, target_id=target_id, status='pending').update(
            status='actioned',
            resolved_by=moderator,
            resolution_notes=f"Action taken: {action} ({reason})",
            resolved_at=timezone.now()
        )

        return ma
