from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q, F
from django.utils import timezone

from backend.judge.models import Profile
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from backend.community.models import (
    Post, Comment, ForumCategory, Thread, ThreadPost,
    Reaction, Follow, Group, GroupMember, Conversation, Message,
    Notification, Report, ModerationAction
)
from backend.community.repositories.post_repository import PostRepository
from backend.community.repositories.comment_repository import CommentRepository
from backend.community.repositories.thread_repository import ThreadRepository
from backend.community.services.feed_service import FeedService
from backend.community.services.reaction_service import ReactionService
from backend.community.services.notification_service import NotificationService
from backend.community.services.moderation_service import ModerationService

from .serializers import (
    PostSerializer, CommentSerializer, ForumCategorySerializer,
    ThreadListSerializer, ThreadDetailSerializer, ThreadPostSerializer,
    GroupSerializer, NotificationSerializer, ConversationSerializer,
    MessageSerializer, ReportSerializer
)


class CommunityAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

def api_response(data=None, error=None, status_code=200):
    if error:
        return Response({'status': status_code, 'error': error}, status=status_code)
    return Response({'status': status_code, 'data': data}, status=status_code)

def get_current_profile(request):
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        return None
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


# ── 1. FEED ─────────────────────────────────────────────────────────────────
class FeedView(CommunityAPIView):
    def get(self, request):
        feed_data = FeedService.get_community_feed()
        from backend.api.v2.serializers import ContestListSerializer, PublicUserProfileSerializer
        return api_response({
            'posts': PostSerializer(feed_data['posts'], many=True).data,
            'trending_threads': ThreadListSerializer(feed_data['trending_threads'], many=True).data,
            'upcoming_contests': ContestListSerializer(feed_data['upcoming_contests'], many=True).data,
            'top_coders': PublicUserProfileSerializer(feed_data['top_coders'], many=True).data
        })


# ── 2. POSTS ────────────────────────────────────────────────────────────────
class PostListView(CommunityAPIView):
    def get(self, request):
        tag = request.GET.get('tag')
        search = request.GET.get('q')
        author = request.GET.get('author')
        qs = PostRepository.get_all(tag=tag, search=search, author=author)

        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 20))))
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size

        serializer = PostSerializer(qs[start:end], many=True)
        return api_response({
            'current_page': page,
            'page_size': page_size,
            'total_objects': total,
            'total_pages': max(1, (total + page_size - 1) // page_size),
            'has_more': end < total,
            'objects': serializer.data
        })

    def post(self, request):
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        if not title or not content:
            return api_response(error={'message': 'Tiêu đề và nội dung bài viết không được để trống'}, status_code=400)

        author = get_current_profile(request)
        if not author:
            return api_response(error={'message': 'Chưa xác thực người dùng'}, status_code=401)

        summary = request.data.get('summary', '') or content[:200]
        tags = request.data.get('tags', [])
        is_pinned = bool(request.data.get('is_pinned', False)) and (author.user.is_staff)

        post = PostRepository.create(
            author=author,
            title=title,
            content=content,
            summary=summary,
            tags=tags,
            is_pinned=is_pinned
        )
        return api_response(PostSerializer(post).data, status_code=201)

class PostDetailView(CommunityAPIView):
    def get(self, request, pk):
        post = get_object_or_404(Post.objects.select_related('author__user'), id=pk, is_hidden=False)
        Post.objects.filter(id=post.id).update(view_count=F('view_count') + 1)
        post.refresh_from_db()
        return api_response(PostSerializer(post).data)

    def patch(self, request, pk):
        post = get_object_or_404(Post, id=pk)
        author = get_current_profile(request)
        if not (author == post.author or author.user.is_staff):
            return api_response(error={'message': 'Bạn không có quyền chỉnh sửa bài viết này'}, status_code=403)

        for field in ['title', 'content', 'summary', 'tags']:
            if field in request.data:
                setattr(post, field, request.data[field])
        post.save()
        return api_response(PostSerializer(post).data)

    def delete(self, request, pk):
        post = get_object_or_404(Post, id=pk)
        author = get_current_profile(request)
        if not (author == post.author or author.user.is_staff):
            return api_response(error={'message': 'Bạn không có quyền xóa bài viết này'}, status_code=403)
        post.is_hidden = True
        post.save(update_fields=['is_hidden'])
        return api_response({'message': 'Đã xóa bài viết thành công'})

class PostPinView(CommunityAPIView):
    def post(self, request, pk):
        post = get_object_or_404(Post, id=pk)
        author = get_current_profile(request)
        if not (author and author.user.is_staff):
            return api_response(error={'message': 'Chỉ quản trị viên mới có thể ghim bài viết'}, status_code=403)
        post.is_pinned = not post.is_pinned
        post.save(update_fields=['is_pinned'])
        return api_response({'message': f'Bài viết đã {"ghim" if post.is_pinned else "bỏ ghim"}', 'is_pinned': post.is_pinned})

class PostCommentsView(CommunityAPIView):
    def get(self, request, pk):
        comments = CommentRepository.get_by_post(pk)
        return api_response({'objects': CommentSerializer(comments, many=True).data})

    def post(self, request, pk):
        post = get_object_or_404(Post, id=pk, is_hidden=False)
        content = request.data.get('content', '').strip()
        if not content:
            return api_response(error={'message': 'Nội dung bình luận không được để trống'}, status_code=400)

        author = get_current_profile(request)
        parent_id = request.data.get('parent')
        parent = Comment.objects.filter(id=parent_id).first() if parent_id else None

        cmt = CommentRepository.create(post=post, author=author, content=content, parent=parent)

        # Notify post author
        NotificationService.notify(
            recipient=post.author,
            sender=author,
            ntype='comment',
            title='Bình luận mới',
            message=f"{author.user.username} đã bình luận vào bài viết của bạn: \"{post.title}\"",
            link=f"/community/posts/detail.html?id={post.id}"
        )
        return api_response(CommentSerializer(cmt).data, status_code=201)


# ── 3. REACTIONS ────────────────────────────────────────────────────────────
class ReactionView(CommunityAPIView):
    def post(self, request):
        target_type = request.data.get('target_type', 'post')
        target_id = int(request.data.get('target_id', 0))
        reaction_type = request.data.get('reaction_type', 'like')

        user = get_current_profile(request)
        result = ReactionService.toggle_reaction(user, target_type, target_id, reaction_type)
        return api_response(result)


# ── 4. FORUM ────────────────────────────────────────────────────────────────
class ForumCategoriesView(CommunityAPIView):
    def get(self, request):
        cats = ForumCategory.objects.filter(is_active=True).order_by('order')
        return api_response({'objects': ForumCategorySerializer(cats, many=True).data})

class ForumCategoryThreadsView(CommunityAPIView):
    def get(self, request, slug):
        cat = get_object_or_404(ForumCategory, slug=slug, is_active=True)
        search = request.GET.get('q')
        threads = ThreadRepository.get_by_category(category_slug=slug, search=search)
        return api_response({
            'category': ForumCategorySerializer(cat).data,
            'threads': ThreadListSerializer(threads, many=True).data
        })

class ForumThreadListView(CommunityAPIView):
    def get(self, request):
        search = request.GET.get('q')
        cat_slug = request.GET.get('category')
        threads = ThreadRepository.get_by_category(category_slug=cat_slug, search=search)
        return api_response({'objects': ThreadListSerializer(threads, many=True).data})

    def post(self, request):
        title = request.data.get('title', '').strip()
        content = request.data.get('content', '').strip()
        cat_slug = request.data.get('category_slug') or request.data.get('category')

        if not title or not content:
            return api_response(error={'message': 'Tiêu đề và nội dung chủ đề không được để trống'}, status_code=400)

        cat = get_object_or_404(ForumCategory, slug=cat_slug)
        author = get_current_profile(request)

        thread = ThreadRepository.create_thread(
            category=cat,
            author=author,
            title=title,
            content=content,
            is_pinned=bool(request.data.get('is_pinned', False)) and author.user.is_staff
        )
        return api_response(ThreadDetailSerializer(thread).data, status_code=201)

class ForumThreadDetailView(CommunityAPIView):
    def get(self, request, pk):
        thread = get_object_or_404(Thread.objects.select_related('author__user', 'category'), id=pk, is_hidden=False)
        Thread.objects.filter(id=thread.id).update(view_count=F('view_count') + 1)
        thread.refresh_from_db()
        return api_response(ThreadDetailSerializer(thread).data)

    def patch(self, request, pk):
        thread = get_object_or_404(Thread, id=pk)
        author = get_current_profile(request)
        if not (author == thread.author or author.user.is_staff):
            return api_response(error={'message': 'Bạn không có quyền chỉnh sửa chủ đề này'}, status_code=403)
        for field in ['title', 'content']:
            if field in request.data:
                setattr(thread, field, request.data[field])
        thread.save()
        return api_response(ThreadDetailSerializer(thread).data)

    def delete(self, request, pk):
        thread = get_object_or_404(Thread, id=pk)
        author = get_current_profile(request)
        if not (author == thread.author or author.user.is_staff):
            return api_response(error={'message': 'Bạn không có quyền xóa chủ đề này'}, status_code=403)
        thread.is_hidden = True
        thread.save(update_fields=['is_hidden'])
        return api_response({'message': 'Đã xóa chủ đề thành công'})

class ForumThreadReplyView(CommunityAPIView):
    def post(self, request, pk):
        thread = get_object_or_404(Thread, id=pk, is_hidden=False)
        if thread.is_locked:
            return api_response(error={'message': 'Chủ đề này đã bị khóa phản hồi'}, status_code=400)

        content = request.data.get('content', '').strip()
        if not content:
            return api_response(error={'message': 'Nội dung phản hồi không được để trống'}, status_code=400)

        author = get_current_profile(request)
        reply = ThreadRepository.add_reply(thread=thread, author=author, content=content)

        # Notify thread author
        NotificationService.notify(
            recipient=thread.author,
            sender=author,
            ntype='reply',
            title='Phản hồi thảo luận',
            message=f"{author.user.username} đã phản hồi chủ đề: \"{thread.title}\"",
            link=f"/community/forum/thread.html?id={thread.id}"
        )
        return api_response(ThreadPostSerializer(reply).data, status_code=201)

class ForumThreadLockView(CommunityAPIView):
    def post(self, request, pk):
        thread = get_object_or_404(Thread, id=pk)
        author = get_current_profile(request)
        if not (author and author.user.is_staff):
            return api_response(error={'message': 'Chỉ quản trị viên mới có thể khóa chủ đề'}, status_code=403)
        thread.is_locked = not thread.is_locked
        thread.save(update_fields=['is_locked'])
        return api_response({'message': f'Chủ đề đã {"khóa" if thread.is_locked else "mở khóa"}', 'is_locked': thread.is_locked})

class ForumThreadPinView(CommunityAPIView):
    def post(self, request, pk):
        thread = get_object_or_404(Thread, id=pk)
        author = get_current_profile(request)
        if not (author and author.user.is_staff):
            return api_response(error={'message': 'Chỉ quản trị viên mới có thể ghim chủ đề'}, status_code=403)
        thread.is_pinned = not thread.is_pinned
        thread.save(update_fields=['is_pinned'])
        return api_response({'message': f'Chủ đề đã {"ghim" if thread.is_pinned else "bỏ ghim"}', 'is_pinned': thread.is_pinned})


# ── 5. GROUPS ───────────────────────────────────────────────────────────────
class GroupListView(CommunityAPIView):
    def get(self, request):
        qs = Group.objects.all().select_related('owner__user').order_by('-member_count')
        return api_response({'objects': GroupSerializer(qs, many=True).data})

    def post(self, request):
        name = request.data.get('name', '').strip()
        slug = request.data.get('slug', '').strip() or name.lower().replace(' ', '-')
        description = request.data.get('description', '')
        author = get_current_profile(request)

        if not name:
            return api_response(error={'message': 'Tên nhóm không được để trống'}, status_code=400)

        group = Group.objects.create(name=name, slug=slug, description=description, owner=author)
        GroupMember.objects.create(group=group, user=author, role='owner')
        return api_response(GroupSerializer(group).data, status_code=201)

class GroupJoinView(CommunityAPIView):
    def post(self, request, pk):
        group = get_object_or_404(Group, id=pk)
        user = get_current_profile(request)
        member, created = GroupMember.objects.get_or_create(group=group, user=user, defaults={'role': 'member'})
        if created:
            group.member_count = group.members.count()
            group.save(update_fields=['member_count'])
        return api_response({'message': f'Đã gia nhập nhóm {group.name}', 'is_member': True})

class GroupLeaveView(CommunityAPIView):
    def post(self, request, pk):
        group = get_object_or_404(Group, id=pk)
        user = get_current_profile(request)
        GroupMember.objects.filter(group=group, user=user).exclude(role='owner').delete()
        group.member_count = group.members.count()
        group.save(update_fields=['member_count'])
        return api_response({'message': f'Đã rời khỏi nhóm {group.name}', 'is_member': False})


# ── 6. DIRECT MESSAGES ──────────────────────────────────────────────────────
class ConversationsView(CommunityAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_current_profile(request)
        convs = Conversation.objects.filter(Q(participant_1=user) | Q(participant_2=user)).select_related('participant_1__user', 'participant_2__user')
        return api_response({'objects': ConversationSerializer(convs, many=True).data})

class MessagesView(CommunityAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        user = get_current_profile(request)
        if user not in [conv.participant_1, conv.participant_2]:
            return api_response(error={'message': 'Không có quyền xem cuộc trò chuyện này'}, status_code=403)
        msgs = conv.messages.select_related('sender__user').order_by('created_at')
        # Mark as read
        conv.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        return api_response({'objects': MessageSerializer(msgs, many=True).data})

    def post(self, request, conversation_id):
        conv = get_object_or_404(Conversation, id=conversation_id)
        user = get_current_profile(request)
        if user not in (conv.participant_1, conv.participant_2):
            return api_response(error={'message': 'Không có quyền gửi tin nhắn vào cuộc trò chuyện này'}, status_code=403)
        content = request.data.get('content', '').strip()
        if not content:
            return api_response(error={'message': 'Nội dung tin nhắn không được để trống'}, status_code=400)

        msg = Message.objects.create(conversation=conv, sender=user, content=content)
        conv.updated_at = timezone.now()
        conv.save(update_fields=['updated_at'])

        # Notify other participant
        recipient = conv.participant_2 if conv.participant_1 == user else conv.participant_1
        NotificationService.notify(
            recipient=recipient,
            sender=user,
            ntype='message',
            title='Tin nhắn mới',
            message=f"{user.user.username}: {content[:60]}",
            link=f"/community/messages/conversation.html?id={conv.id}"
        )
        return api_response(MessageSerializer(msg).data, status_code=201)

class StartConversationView(CommunityAPIView):
    def post(self, request):
        user = get_current_profile(request)
        target_username = request.data.get('target_user')
        target_user = get_object_or_404(Profile, user__username=target_username)

        if user == target_user:
            return api_response(error={'message': 'Không thể nhắn tin cho chính mình'}, status_code=400)

        p1, p2 = (user, target_user) if user.id < target_user.id else (target_user, user)
        conv, created = Conversation.objects.get_or_create(participant_1=p1, participant_2=p2)

        init_msg = request.data.get('content', '').strip()
        if init_msg:
            Message.objects.create(conversation=conv, sender=user, content=init_msg)

        return api_response(ConversationSerializer(conv).data, status_code=201 if created else 200)


# ── 7. NOTIFICATIONS ────────────────────────────────────────────────────────
class NotificationsView(CommunityAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = get_current_profile(request)
        unread_only = request.GET.get('unread') == 'true'
        notifs = NotificationService.get_user_notifications(user, unread_only=unread_only)
        return api_response({
            'unread_count': notifs.filter(is_read=False).count(),
            'objects': NotificationSerializer(notifs[:30], many=True).data
        })

class NotificationReadView(CommunityAPIView):
    def post(self, request, pk):
        user = get_current_profile(request)
        Notification.objects.filter(id=pk, recipient=user).update(is_read=True)
        return api_response({'message': 'Đã đánh dấu đã đọc'})

class NotificationReadAllView(CommunityAPIView):
    def post(self, request):
        user = get_current_profile(request)
        NotificationService.mark_all_read(user)
        return api_response({'message': 'Đã đánh dấu đã đọc tất cả thông báo'})


# ── 8. SEARCH ───────────────────────────────────────────────────────────────
class SearchView(CommunityAPIView):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        if not q:
            return api_response({'posts': [], 'threads': [], 'users': []})

        posts = Post.objects.filter(Q(title__icontains=q) | Q(content__icontains=q), is_hidden=False)[:10]
        threads = Thread.objects.filter(Q(title__icontains=q) | Q(content__icontains=q), is_hidden=False)[:10]
        users = Profile.objects.filter(Q(user__username__icontains=q) | Q(about__icontains=q))[:10]

        from backend.api.v2.serializers import PublicUserProfileSerializer
        return api_response({
            'posts': PostSerializer(posts, many=True).data,
            'threads': ThreadListSerializer(threads, many=True).data,
            'users': PublicUserProfileSerializer(users, many=True).data
        })


# ── 9. REPORTS & MODERATION ─────────────────────────────────────────────────
class ReportsView(CommunityAPIView):
    def get(self, request):
        author = get_current_profile(request)
        if not (author and author.user.is_staff):
            return api_response(error={'message': 'Chỉ quản trị viên mới có quyền xem danh sách báo cáo'}, status_code=403)
        reports = ModerationService.get_pending_reports()
        return api_response({'objects': ReportSerializer(reports, many=True).data})

    def post(self, request):
        target_type = request.data.get('target_type')
        target_id = int(request.data.get('target_id', 0))
        reason = request.data.get('reason', '').strip()
        details = request.data.get('details', '').strip()

        if not target_type or not target_id or not reason:
            return api_response(error={'message': 'Vui lòng cung cấp lý do báo cáo vi phạm'}, status_code=400)

        reporter = get_current_profile(request)
        rep = ModerationService.create_report(reporter, target_type, target_id, reason, details)
        return api_response(ReportSerializer(rep).data, status_code=201)

class ModerationActionView(CommunityAPIView):
    def post(self, request):
        author = get_current_profile(request)
        if not (author and author.user.is_staff):
            return api_response(error={'message': 'Chỉ quản trị viên mới có quyền thực hiện kiểm duyệt'}, status_code=403)

        target_type = request.data.get('target_type')
        target_id = int(request.data.get('target_id', 0))
        action = request.data.get('action') # hide, restore, lock, pin, ban
        reason = request.data.get('reason', 'Kiểm duyệt nội dung')

        act = ModerationService.apply_action(author, target_type, target_id, action, reason)
        return api_response({'message': f'Đã thực hiện thao tác kiểm duyệt: {action}', 'action_id': act.id})


# ── 10. USER SOCIAL ─────────────────────────────────────────────────────────
class UserCommunityProfileView(CommunityAPIView):
    def get(self, request, username):
        user_prof = get_object_or_404(Profile.objects.select_related('user'), user__username=username)
        from backend.api.v2.serializers import PublicUserProfileSerializer
        data = PublicUserProfileSerializer(user_prof).data

        data['posts_count'] = Post.objects.filter(author=user_prof, is_hidden=False).count()
        data['threads_count'] = Thread.objects.filter(author=user_prof, is_hidden=False).count()
        data['followers_count'] = Follow.objects.filter(following=user_prof).count()
        data['following_count'] = Follow.objects.filter(follower=user_prof).count()

        recent_posts = Post.objects.filter(author=user_prof, is_hidden=False).order_by('-created_at')[:5]
        data['recent_posts'] = PostSerializer(recent_posts, many=True).data

        recent_threads = Thread.objects.filter(author=user_prof, is_hidden=False).order_by('-created_at')[:5]
        data['recent_threads'] = ThreadListSerializer(recent_threads, many=True).data

        return api_response({'object': data})

class UserFollowView(CommunityAPIView):
    def post(self, request, username):
        target_prof = get_object_or_404(Profile, user__username=username)
        current = get_current_profile(request)
        if current == target_prof:
            return api_response(error={'message': 'Không thể theo dõi chính mình'}, status_code=400)

        follow_obj = Follow.objects.filter(follower=current, following=target_prof).first()
        if follow_obj:
            follow_obj.delete()
            following = False
        else:
            Follow.objects.create(follower=current, following=target_prof)
            following = True
            NotificationService.notify(
                recipient=target_prof,
                sender=current,
                ntype='follow',
                title='Người theo dõi mới',
                message=f"{current.user.username} đã bắt đầu theo dõi bạn.",
                link=f"/community/users/profile.html?u={current.user.username}"
            )

        followers_cnt = Follow.objects.filter(following=target_prof).count()
        return api_response({'following': following, 'followers_count': followers_cnt})
