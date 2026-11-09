from django.db.models import Q
from backend.community.models import Post

class PostRepository:
    @staticmethod
    def get_all(tag=None, search=None, author=None, include_hidden=False):
        qs = Post.objects.select_related('author__user').all()
        if not include_hidden:
            qs = qs.filter(is_hidden=False)
        if tag:
            qs = qs.filter(tags__contains=tag)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(content__icontains=search))
        if author:
            qs = qs.filter(author__user__username=author)
        return qs

    @staticmethod
    def get_by_id(post_id, include_hidden=False):
        qs = Post.objects.select_related('author__user')
        if not include_hidden:
            qs = qs.filter(is_hidden=False)
        return qs.filter(id=post_id).first()

    @staticmethod
    def get_by_slug(slug, include_hidden=False):
        qs = Post.objects.select_related('author__user')
        if not include_hidden:
            qs = qs.filter(is_hidden=False)
        return qs.filter(slug=slug).first()

    @staticmethod
    def create(author, title, content, summary="", tags=None, is_pinned=False):
        import uuid
        slug_base = title.lower().replace(' ', '-')[:120]
        # Ensure unique slug
        slug = f"{slug_base}-{uuid.uuid4().hex[:6]}"
        return Post.objects.create(
            author=author,
            title=title,
            slug=slug,
            content=content,
            summary=summary or content[:200],
            tags=tags or [],
            is_pinned=is_pinned
        )
