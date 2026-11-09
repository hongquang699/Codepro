from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User

class ProfileBlogAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        posts = []
        try:
            from backend.community.models import Post
            community_posts = Post.objects.filter(author=user).order_by('-created_at')[:20]
            for p in community_posts:
                posts.append({
                    'id': p.id,
                    'title': p.title,
                    'excerpt': (p.content[:150] + '...') if len(p.content) > 150 else p.content,
                    'created_at': p.created_at.strftime('%d/%m/%Y'),
                    'views': getattr(p, 'views', 0),
                    'likes': getattr(p, 'likes_count', 0),
                    'link': f"/community/post/{p.id}"
                })
        except Exception:
            pass

        return Response({
            'status': 'success',
            'total': len(posts),
            'results': posts
        })
