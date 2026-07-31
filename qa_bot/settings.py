"""
Django settings for the Document Q&A Bot project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Core / security
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-insecure-key-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Render sets this automatically for every deploy - add it so Django accepts
# requests to your live *.onrender.com URL.
RENDER_EXTERNAL_HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS = [f'https://{RENDER_EXTERNAL_HOSTNAME}']

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'corsheaders',

    'documents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'qa_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'qa_bot.wsgi.application'

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Defaults to SQLite for local dev. If a DATABASE_URL is set (Render provides
# one automatically when you attach a Postgres instance), that's used instead -
# recommended for deployment, since SQLite lives on disk that Render's free
# tier wipes on every redeploy.
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static & media files
# ---------------------------------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'documents' / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# CORS (only needed if you later split the frontend onto its own dev server)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
}

# ---------------------------------------------------------------------------
# Upload limits
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = 15
ALLOWED_UPLOAD_EXTENSIONS = ['.pdf', '.docx']

# ---------------------------------------------------------------------------
# Gemini / RAG configuration
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/gemini-embedding-001')
CHAT_MODEL = os.getenv('CHAT_MODEL', 'models/gemini-flash-latest')

CHUNK_SIZE_TOKENS = int(os.getenv('CHUNK_SIZE_TOKENS', 350))
CHUNK_OVERLAP_TOKENS = int(os.getenv('CHUNK_OVERLAP_TOKENS', 50))
TOP_K_CHUNKS = int(os.getenv('TOP_K_CHUNKS', 4))

VECTOR_INDEX_DIR = BASE_DIR / 'vector_indexes'
