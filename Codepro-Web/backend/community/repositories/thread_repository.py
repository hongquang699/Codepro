from django.db.models import Q
from backend.community.models import Thread, ThreadPost

class ThreadRepository:
    @staticmethod
    def get_by_category(category_slug=None, search=None):
        qs = Thread.objects.select_related('author__user', 'category').filter(is_hidden=False)
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
        return qs

    @staticmethod
    def get_by_id(thread_id):
        return Thread.objects.select_related('author__user', 'category').filter(id=thread_id, is_hidden=False).first()

    @staticmethod
    def create_thread(category, author, title, content, is_pinned=False):
        thread = Thread.objects.create(category=category, author=author, title=title, content=content, is_pinned=is_pinned)
        category.thread_count = category.threads.count()
        category.save(update_fields=['thread_count'])
        return thread

    @staticmethod
    def add_reply(thread, author, content):
        reply = ThreadPost.objects.create(thread=thread, author=author, content=content)
        thread.reply_count = thread.posts.count()
        from django.utils import timezone
        thread.last_activity_at = timezone.now()
        thread.save(update_fields=['reply_count', 'last_activity_at'])
        thread.category.post_count += 1
        thread.category.save(update_fields=['post_count'])
        return reply
