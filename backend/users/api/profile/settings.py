from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from backend.auth.security.token_auth import ExpiringTokenAuthentication as TokenAuthentication
from backend.judge.permissions.authentication import BearerTokenAuthentication, JudgeCookieAuthentication
from ...models import UserSettings

class ProfileSettingsAPIView(APIView):
    authentication_classes = [TokenAuthentication, BearerTokenAuthentication, JudgeCookieAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def _verify_owner(self, request, target_user):
        return request.user == target_user or request.user.is_staff or request.user.is_superuser

    def get(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if not self._verify_owner(request, user):
            return Response({'error': 'Từ chối truy cập: Bạn chỉ có thể xem cài đặt tài khoản của chính mình'}, status=status.HTTP_403_FORBIDDEN)

        st, _ = UserSettings.objects.get_or_create(user=user)
        return Response({
            'status': 'success',
            'settings': {
                'account': {
                    'username': user.username,
                    'email': user.email,
                    'is_staff': user.is_staff
                },
                'preferences': {
                    'language': st.language,
                    'theme': st.theme,
                    'editor_theme': st.editor_theme,
                    'editor_keymap': st.editor_keymap,
                    'tab_size': st.tab_size,
                    'default_code_language': st.default_code_language,
                    'timezone': st.timezone,
                },
                'notifications': {
                    'email_notifications': st.email_notifications,
                    'contest_notifications': st.contest_notifications,
                    'system_notifications': st.system_notifications,
                },
                'privacy': {
                    'privacy_profile': st.privacy_profile,
                    'privacy_submissions': st.privacy_submissions,
                    'privacy_activity': st.privacy_activity,
                },
                'security': {
                    'two_factor_enabled': st.two_factor_enabled,
                }
            }
        })

    def patch(self, request, username):
        user = User.objects.filter(username=username).first()
        if not user:
            return Response({'error': 'Người dùng không tồn tại'}, status=status.HTTP_404_NOT_FOUND)

        if not self._verify_owner(request, user):
            return Response({'error': 'Từ chối truy cập: Bạn chỉ có thể cập nhật cài đặt của chính mình'}, status=status.HTTP_403_FORBIDDEN)

        st, _ = UserSettings.objects.get_or_create(user=user)
        data = request.data
        acc = data.get('account', {})
        if acc.get('password') and request.user == user and not user.check_password(acc.get('current_password', '')):
            return Response({'error': 'Mật khẩu hiện tại không đúng'}, status=status.HTTP_400_BAD_REQUEST)

        # Update preferences
        pref = data.get('preferences', {})
        for field in ['language', 'theme', 'editor_theme', 'editor_keymap', 'tab_size', 'default_code_language', 'timezone']:
            if field in pref:
                setattr(st, field, pref[field])

        # Update notifications
        noti = data.get('notifications', {})
        for field in ['email_notifications', 'contest_notifications', 'system_notifications']:
            if field in noti:
                setattr(st, field, bool(noti[field]))

        # Update privacy
        priv = data.get('privacy', {})
        for field in ['privacy_profile', 'privacy_submissions', 'privacy_activity']:
            if field in priv:
                setattr(st, field, priv[field])

        # Update email if provided
        if 'email' in acc and acc['email']:
            user.email = acc['email']
            user.save(update_fields=['email'])

        # Update password if requested
        if 'password' in acc and acc['password']:
            user.set_password(acc['password'])
            user.save()

        st.save()

        return Response({
            'status': 'success',
            'message': 'Cài đặt đã được lưu thành công'
        })
