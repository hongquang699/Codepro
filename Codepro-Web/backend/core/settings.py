import os
from pathlib import Path
from urllib.parse import urlsplit

BASE_DIR = Path(__file__).resolve().parent.parent.parent

def _load_project_env(path: Path) -> None:
    """Load simple KEY=value entries without overriding process environment."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)

_load_project_env(BASE_DIR / '.env')

def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')

SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError('SECRET_KEY must be set in the environment or project .env file')
DEBUG = _env_bool('DEBUG')
_allowed_hosts_env = os.getenv('ALLOWED_HOSTS')
ALLOWED_HOSTS = [
    host.strip() for host in (
        _allowed_hosts_env.split(',') if _allowed_hosts_env is not None else
        ['localhost', '127.0.0.1', 'codeprooj.com', 'www.codeprooj.com']
    ) if host.strip()
]
if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError('ALLOWED_HOSTS must contain at least one host in production')
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise RuntimeError('Wildcard ALLOWED_HOSTS is not permitted in production')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'backend.judge.apps.JudgeAppConfig',
    'backend.problem_storage.apps.ProblemStorageConfig',
    'backend.api.apps.ApiConfig',
    'backend.community.apps.CommunityConfig',
    'backend.ranking.apps.RankingConfig',
    'backend.users.apps.UsersConfig',
    'backend.organizations.apps.OrganizationsConfig',
    'backend.contest_admin.apps.ContestAdminConfig',
    'backend.anti_cheat.apps.AntiCheatConfig',
    'backend.auth.apps.AuthConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'security.middleware.FullSecurityMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'backend', 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

CSRF_TRUSTED_ORIGINS = [
    'https://codeprooj.com',
    'http://codeprooj.com',
    'https://www.codeprooj.com',
    'http://www.codeprooj.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:8888',
    'http://127.0.0.1:8888',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]

WSGI_APPLICATION = 'backend.core.wsgi.application'
ASGI_APPLICATION = 'backend.core.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer' if os.getenv('REDIS_URL') else 'channels.layers.InMemoryChannelLayer',
        'CONFIG': {'hosts': [os.environ['REDIS_URL']]} if os.getenv('REDIS_URL') else {},
    }
}

DB_ENGINE = os.getenv('DB_ENGINE', '').lower()
DB_HOST = os.getenv('DB_HOST', '')

if DB_ENGINE in ('mysql', 'mariadb'):
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME', 'coding_platform'),
            'USER': os.getenv('DB_USER', 'coding_app'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': DB_HOST or 'localhost',
            'PORT': os.getenv('DB_PORT', '3306'),
            'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION'",
            }
        }
    }
elif DB_ENGINE in ('postgresql', 'postgres', 'pgsql') or DB_HOST:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'coding_platform'),
            'USER': os.getenv('DB_USER', 'judge_admin'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': DB_HOST or 'localhost',
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'database' / 'vnoi_db.sqlite3',
            'OPTIONS': {
                'timeout': 30,
            },
        }
    }

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 6}},
]

LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'frontend')] if DEBUG else []

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'storage'

PROBLEM_STORAGE_ENDPOINT = os.getenv('PROBLEM_STORAGE_ENDPOINT', '')
PROBLEM_STORAGE_PUBLIC_ENDPOINT = os.getenv('PROBLEM_STORAGE_PUBLIC_ENDPOINT', PROBLEM_STORAGE_ENDPOINT)
PROBLEM_STORAGE_ACCESS_KEY = os.getenv('PROBLEM_STORAGE_ACCESS_KEY', '')
PROBLEM_STORAGE_SECRET_KEY = os.getenv('PROBLEM_STORAGE_SECRET_KEY', '')
PROBLEM_STORAGE_PRIVATE_BUCKET = os.getenv('PROBLEM_STORAGE_PRIVATE_BUCKET', 'problem-private')
PROBLEM_STORAGE_PUBLIC_BUCKET = os.getenv('PROBLEM_STORAGE_PUBLIC_BUCKET', 'problem-public')
PROBLEM_STORAGE_QUEUE_URL = os.getenv('PROBLEM_STORAGE_QUEUE_URL', '')
PROBLEM_STORAGE_INTERNAL_TOKEN = os.getenv('PROBLEM_STORAGE_INTERNAL_TOKEN', '')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Outbound account email must use a configured delivery service in production.
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '25'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = _env_bool('EMAIL_USE_TLS', False)
EMAIL_USE_SSL = _env_bool('EMAIL_USE_SSL', False)
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@codeprooj.com')

# New passwords use Argon2id; existing hashes remain verifiable and are upgraded on login.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'backend.auth.security.crypto_hash.PBKDF2SHA512PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',              # PBKDF2 with HMAC-SHA256 (Compatibility)
    'backend.auth.security.crypto_hash.SHA512PasswordHasher',        # Salted SHA-512
    'backend.auth.security.crypto_hash.SHA256PasswordHasher',        # Salted SHA-256
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

# ── CORS & CSRF Origins: explicit origins only; wildcard+credentials is forbidden ──
def _validated_origins(env_name, defaults, *, allow_http):
    values = list(defaults)
    configured = os.getenv(env_name, '')
    if configured:
        values.extend(item.strip() for item in configured.split(',') if item.strip())

    origins = []
    for value in values:
        parsed = urlsplit(value)
        try:
            parsed.port  # Validate that any explicit port is syntactically valid.
        except ValueError:
            raise RuntimeError(f'{env_name} contains an invalid origin: {value!r}') from None
        if (parsed.scheme not in (('https', 'http') if allow_http else ('https',))
                or not parsed.hostname or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password or '*' in value):
            raise RuntimeError(f'{env_name} contains an invalid or insecure origin: {value!r}')
        try:
            hostname = parsed.hostname.encode('idna').decode('ascii').lower()
        except UnicodeError:
            raise RuntimeError(f'{env_name} contains an invalid origin: {value!r}') from None
        if ':' in hostname:
            hostname = f'[{hostname}]'
        default_port = 80 if parsed.scheme == 'http' else 443
        port_suffix = f':{parsed.port}' if parsed.port and parsed.port != default_port else ''
        normalized = f'{parsed.scheme}://{hostname}{port_suffix}'
        if normalized not in origins:
            origins.append(normalized)
    return origins

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = _validated_origins(
    'CORS_ALLOWED_ORIGINS',
    ['https://codeprooj.com', 'https://www.codeprooj.com'] + ([
        'http://localhost:8888', 'http://127.0.0.1:8888',
        'http://localhost:8000', 'http://127.0.0.1:8000',
        'http://localhost:3000', 'http://127.0.0.1:3000',
    ] if DEBUG else []),
    allow_http=DEBUG,
)

CSRF_TRUSTED_ORIGINS = _validated_origins(
    'CSRF_TRUSTED_ORIGINS',
    ['https://codeprooj.com', 'https://www.codeprooj.com'] + ([
        'http://localhost:8888', 'http://127.0.0.1:8888',
        'http://localhost:8000', 'http://127.0.0.1:8000',
        'http://localhost:3000', 'http://127.0.0.1:3000',
    ] if DEBUG else []),
    allow_http=DEBUG,
)

# ── Security & Cookie Hardening (XSS, CSRF, Clickjacking) ─────────────────────
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 60 * 60 * 24
CSRF_COOKIE_SAMESITE = 'Lax'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production HTTPS & HSTS Settings (Activated when DEBUG is False)
if not DEBUG:
    if _env_bool('TRUST_PROXY_SSL_HEADER'):
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False


REST_FRAMEWORK_RENDERERS = ['rest_framework.renderers.JSONRenderer']
if DEBUG:
    REST_FRAMEWORK_RENDERERS.append('rest_framework.renderers.BrowsableAPIRenderer')

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'backend.auth.security.token_auth.ExpiringTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': REST_FRAMEWORK_RENDERERS
}

# Problem and contest files live outside the source checkout.
CODEPRO_DATA_ROOT = Path(os.getenv('CODEPRO_DATA_ROOT') or BASE_DIR.parent.parent / 'Codepro-Data').resolve()
DMOJ_PROBLEM_DATA_ROOT = os.getenv(
    'DMOJ_PROBLEM_DATA_ROOT', str(CODEPRO_DATA_ROOT / 'problem-data' / 'problems'))
DMOJ_CONTEST_DATA_ROOT = os.getenv(
    'DMOJ_CONTEST_DATA_ROOT', str(CODEPRO_DATA_ROOT / 'contest-data' / 'contests'))
CODEPRO_CONTEST_PACKAGE_ROOT = os.getenv(
    'CODEPRO_CONTEST_PACKAGE_ROOT', str(CODEPRO_DATA_ROOT / 'storage' / 'contests'))

# ── Judge System Integration ──────────────────────────────────────────────────
# External judge-system REST API (port 9999)
JUDGE_SERVER_URL  = os.getenv('JUDGE_SERVER_URL', 'http://127.0.0.1:9999')
JUDGE_AUTH_TOKEN  = os.getenv('JUDGE_AUTH_TOKEN', '')
JUDGE_POLL_TIMEOUT   = int(os.getenv('JUDGE_POLL_TIMEOUT', '30'))   # max seconds to wait
JUDGE_POLL_INTERVAL  = float(os.getenv('JUDGE_POLL_INTERVAL', '0.5'))  # seconds between polls
