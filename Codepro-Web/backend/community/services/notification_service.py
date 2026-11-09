from backend.community.models import Notification

class NotificationService:
    @staticmethod
    def notify(recipient, sender, ntype, title, message, link=""):
        if recipient == sender:
            return None # Don't notify oneself
        return Notification.objects.create(
            recipient=recipient,
            sender=sender,
            notification_type=ntype,
            title=title,
            message=message,
            link=link
        )

    @staticmethod
    def get_user_notifications(profile, unread_only=False):
        qs = Notification.objects.filter(recipient=profile).select_related('sender__user')
        if unread_only:
            qs = qs.filter(is_read=False)
        return qs

    @staticmethod
    def mark_all_read(profile):
        Notification.objects.filter(recipient=profile, is_read=False).update(is_read=True)
