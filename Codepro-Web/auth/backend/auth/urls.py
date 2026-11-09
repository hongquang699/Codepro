from django.urls import path
from .api import (
    register_view,
    resend_verification_view,
    verify_email_view,
    login_view,
    verify_2fa_login_view,
    logout_view,
    me_view,
    forgot_password_view,
    check_reset_token_view,
    reset_password_view,
    change_password_view,
    status_2fa_view,
    setup_2fa_view,
    enable_2fa_view,
    disable_2fa_view,
    list_sessions_view,
    revoke_other_sessions_view,
    revoke_session_by_id_view,
)

urlpatterns = [
    # Registration & Email OTP
    path('register', register_view, name='auth_register'),
    path('resend-verification', resend_verification_view, name='auth_resend_verification'),
    path('verify-email', verify_email_view, name='auth_verify_email'),

    # Authentication & Session
    path('login', login_view, name='auth_login'),
    path('logout', logout_view, name='auth_logout'),
    path('me', me_view, name='auth_me'),

    # Password Management
    path('forgot-password', forgot_password_view, name='auth_forgot_password'),
    path('reset-password', reset_password_view, name='auth_reset_password'),
    path('reset-password/validate', check_reset_token_view, name='auth_check_reset_token'),
    path('change-password', change_password_view, name='auth_change_password'),

    # Two-Factor Authentication
    path('2fa/status', status_2fa_view, name='auth_2fa_status'),
    path('2fa/setup', setup_2fa_view, name='auth_2fa_setup'),
    path('2fa/enable', enable_2fa_view, name='auth_2fa_enable'),
    path('2fa/disable', disable_2fa_view, name='auth_2fa_disable'),
    path('2fa/verify-login', verify_2fa_login_view, name='auth_2fa_verify_login'),

    # Session Management
    path('sessions', list_sessions_view, name='auth_sessions'),
    path('sessions/revoke-others', revoke_other_sessions_view, name='auth_revoke_other_sessions'),
    path('sessions/<int:session_id>/revoke', revoke_session_by_id_view, name='auth_revoke_session_by_id'),
]
