from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from backend.users.models.profile import UserProfile
from backend.auth.models.email_verification import EmailVerification
from backend.auth.validators.registration import validate_registration_payload
from backend.auth.security.token import generate_otp, hash_token, verify_token
from backend.auth.security.rate_limit import check_otp_resend_cooldown, check_verification_rate_limit
from backend.auth.services.email import send_verification_otp_email

OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 5


def initiate_registration(data: dict, ip_address: str = "127.0.0.1") -> tuple[bool, str, dict]:
    """
    Validate registration data, hash password & OTP, store verification record,
    and dispatch OTP email.
    Returns (success, message, extra_info_or_errors).
    """
    is_valid, errors = validate_registration_payload(data)
    if not is_valid:
        return False, "Dữ liệu đăng ký không hợp lệ.", errors

    username = data['username'].strip()
    email = data['email'].strip().lower()
    raw_password = data['password']

    # Rate limiting
    if not check_verification_rate_limit(ip_address, email):
        return False, "Bạn đã gửi quá nhiều yêu cầu đăng ký. Vui lòng thử lại sau 1 giờ.", {}

    # Check cooldown if already requested
    can_resend, wait_sec = check_otp_resend_cooldown(email)
    if not can_resend:
        return False, f"Vui lòng đợi {wait_sec} giây trước khi yêu cầu mã mới.", {'wait_seconds': wait_sec}

    # Generate 6-digit OTP
    otp = generate_otp(6)
    otp_hash = hash_token(otp)
    password_hash = make_password(raw_password)

    expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Invalidate previous unverified records for this email
    EmailVerification.objects.filter(email=email, verified_at__isnull=True).delete()

    verification = EmailVerification.objects.create(
        username=username,
        email=email,
        password_hash=password_hash,
        otp_hash=otp_hash,
        ip_address=ip_address,
        expires_at=expires_at,
        attempts=0
    )

    # Dispatch email
    send_verification_otp_email(email, username, otp)

    return True, "Mã xác thực OTP đã được gửi đến email của bạn.", {
        'email': email,
        'username': username,
        'expires_in_seconds': OTP_EXPIRY_MINUTES * 60,
        'cooldown_seconds': 60
    }


def verify_registration_otp(email: str, otp: str) -> tuple[bool, str, User | None]:
    """
    Validate the 6-digit OTP and provision the active user account.
    Returns (success, message, user_instance).
    """
    if not email or not otp:
        return False, "Email và mã OTP không được để trống.", None

    clean_email = email.strip().lower()
    clean_otp = otp.strip()

    verification = EmailVerification.objects.filter(
        email=clean_email,
        verified_at__isnull=True
    ).order_by('-created_at').first()

    if not verification:
        return False, "Không tìm thấy yêu cầu xác thực hợp lệ hoặc mã đã hết hạn.", None

    if verification.is_expired:
        return False, "Mã OTP đã hết hạn. Vui lòng gửi lại mã mới.", None

    if verification.attempts >= MAX_OTP_ATTEMPTS:
        return False, "Bạn đã nhập sai mã quá 5 lần. Vui lòng gửi lại mã xác thực mới.", None

    # Verify constant-time
    if not verify_token(clean_otp, verification.otp_hash):
        verification.attempts += 1
        verification.save(update_fields=['attempts'])
        remaining = MAX_OTP_ATTEMPTS - verification.attempts
        return False, f"Mã OTP không chính xác. Bạn còn {remaining} lần thử.", None

    # Check if user with this username or email was created in the meantime
    if User.objects.filter(username__iexact=verification.username).exists():
        return False, "Tên đăng nhập này đã được sử dụng.", None
    if User.objects.filter(email__iexact=verification.email).exists():
        return False, "Địa chỉ email này đã được sử dụng.", None

    # Create the User
    user = User(
        username=verification.username,
        email=verification.email,
        password=verification.password_hash,
        is_active=True
    )
    user.save()

    # Create UserProfile if not exists
    UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'display_name': verification.username,
        }
    )

    # Mark verification as fulfilled
    verification.verified_at = timezone.now()
    verification.save(update_fields=['verified_at'])

    return True, "Xác thực email thành công! Tài khoản của bạn đã được kích hoạt.", user


def resend_registration_otp(email: str, ip_address: str = "127.0.0.1") -> tuple[bool, str, int]:
    """
    Generate and resend a new OTP if cooldown has elapsed.
    Returns (success, message, wait_seconds).
    """
    if not email:
        return False, "Email không được để trống.", 0

    clean_email = email.strip().lower()

    verification = EmailVerification.objects.filter(
        email=clean_email,
        verified_at__isnull=True
    ).order_by('-created_at').first()

    if not verification:
        return False, "Không tìm thấy thông tin đăng ký chờ xác nhận.", 0

    can_resend, wait_sec = check_otp_resend_cooldown(clean_email)
    if not can_resend:
        return False, f"Vui lòng đợi {wait_sec} giây trước khi gửi lại.", wait_sec

    # Generate new OTP
    otp = generate_otp(6)
    verification.otp_hash = hash_token(otp)
    verification.expires_at = timezone.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)
    verification.attempts = 0
    verification.created_at = timezone.now()
    verification.save()

    send_verification_otp_email(clean_email, verification.username, otp)

    return True, "Mã xác thực mới đã được gửi thành công.", 60
