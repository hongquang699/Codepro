from backend.community.models import Comment

class CommentRepository:
    @staticmethod
    def get_by_post(post_id, include_hidden=False):
        qs = Comment.objects.filter(post_id=post_id).select_related('author__user', 'parent')
        if not include_hidden:
            qs = qs.filter(is_hidden=False)
        return qs

    @staticmethod
    def create(post, author, content, parent=None):
        cmt = Comment.objects.create(post=post, author=author, content=content, parent=parent)
        post.comment_count = post.comments.count()
        post.save(update_fields=['comment_count'])
        return cmt
