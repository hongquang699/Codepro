from backend.community.models import Reaction, Post, Comment, ThreadPost

class ReactionService:
    @staticmethod
    def toggle_reaction(user, target_type, target_id, reaction_type='like'):
        existing = Reaction.objects.filter(
            user=user,
            target_type=target_type,
            target_id=target_id,
            reaction_type=reaction_type
        ).first()

        if existing:
            existing.delete()
            added = False
        else:
            Reaction.objects.create(
                user=user,
                target_type=target_type,
                target_id=target_id,
                reaction_type=reaction_type
            )
            added = True

        # Update cached like count on target object
        count = Reaction.objects.filter(target_type=target_type, target_id=target_id).count()
        if target_type == 'post':
            Post.objects.filter(id=target_id).update(like_count=count)
        elif target_type == 'comment':
            Comment.objects.filter(id=target_id).update(like_count=count)
        elif target_type in ['thread_post', 'post_reply']:
            ThreadPost.objects.filter(id=target_id).update(like_count=count)

        return {'added': added, 'reaction_count': count, 'reaction_type': reaction_type}
