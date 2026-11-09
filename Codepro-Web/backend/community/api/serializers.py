from rest_framework import serializers
from backend.community.models import (
    Post, Comment, ForumCategory, Thread, ThreadPost,
    Reaction, Follow, Group, GroupMember, Conversation, Message,
    Notification, Report
)

class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.user.username', read_only=True)
    author_rank = serializers.CharField(source='author.display_rank', read_only=True)
    author_rating = serializers.IntegerField(source='author.rating', read_only=True)

    class Meta:
        model = Post
        fields = [
            'id', 'author_username', 'author_rank', 'author_rating',
            'title', 'slug', 'content', 'summary', 'tags',
            'is_pinned', 'like_count', 'comment_count', 'view_count',
            'created_at', 'updated_at'
        ]

class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.user.username', read_only=True)
    author_rank = serializers.CharField(source='author.display_rank', read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author_username', 'author_rank',
            'content', 'parent', 'like_count', 'created_at', 'updated_at'
        ]

class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'slug', 'description', 'icon', 'order', 'thread_count', 'post_count']

class ThreadPostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.user.username', read_only=True)
    author_rank = serializers.CharField(source='author.display_rank', read_only=True)

    class Meta:
        model = ThreadPost
        fields = ['id', 'thread', 'author_username', 'author_rank', 'content', 'is_solution', 'like_count', 'created_at']

class ThreadListSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.user.username', read_only=True)
    author_rank = serializers.CharField(source='author.display_rank', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)

    class Meta:
        model = Thread
        fields = [
            'id', 'category_name', 'category_slug', 'author_username', 'author_rank',
            'title', 'is_pinned', 'is_locked', 'view_count', 'reply_count',
            'last_activity_at', 'created_at'
        ]

class ThreadDetailSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source='author.user.username', read_only=True)
    author_rank = serializers.CharField(source='author.display_rank', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    posts = ThreadPostSerializer(many=True, read_only=True)

    class Meta:
        model = Thread
        fields = [
            'id', 'category_name', 'category_slug', 'author_username', 'author_rank',
            'title', 'content', 'is_pinned', 'is_locked', 'view_count', 'reply_count',
            'posts', 'last_activity_at', 'created_at'
        ]

class GroupSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.user.username', read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'slug', 'description', 'avatar_url', 'owner_username', 'is_private', 'member_count', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.user.username', read_only=True)

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'sender_username', 'title', 'message', 'link', 'is_read', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.user.username', read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'conversation', 'sender_username', 'content', 'is_read', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    p1 = serializers.CharField(source='participant_1.user.username', read_only=True)
    p2 = serializers.CharField(source='participant_2.user.username', read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'p1', 'p2', 'updated_at', 'last_message']

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        return MessageSerializer(last).data if last else None

class ReportSerializer(serializers.ModelSerializer):
    reporter_username = serializers.CharField(source='reporter.user.username', read_only=True)

    class Meta:
        model = Report
        fields = ['id', 'reporter_username', 'target_type', 'target_id', 'reason', 'details', 'status', 'created_at']
