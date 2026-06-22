import os
import pymysql
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-key-for-development')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# ================= INSTALAR PYMYSQL =================
try:
    pymysql.install_as_MySQLdb()
except:
    pass

# ================= APLICACIONES =================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'inventario_app',
]

# ================= MIDDLEWARE =================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mysite.urls'

# ================= TEMPLATES =================
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

WSGI_APPLICATION = 'mysite.wsgi.application'

# ================= BASE DE DATOS =================
# ✅ DEFINIR DATABASE_URL ANTES DE USARLA
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # ✅ ELIMINAR ?ssl-mode=REQUIRED SI EXISTE
    if '?ssl-mode=REQUIRED' in DATABASE_URL:
        DATABASE_URL = DATABASE_URL.replace('?ssl-mode=REQUIRED', '')
    
    if DATABASE_URL.endswith('?ssl-mode=REQUIRED'):
        DATABASE_URL = DATABASE_URL.replace('?ssl-mode=REQUIRED', '')
    
    pattern = r'mysql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
    match = re.match(pattern, DATABASE_URL)
    
    if match:
        user, password, host, port, database = match.groups()
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': database,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': port,
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                },
                'CONN_MAX_AGE': 600,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': os.environ.get('DB_NAME', 'inventario'),
                'USER': os.environ.get('DB_USER', 'admin'),
                'PASSWORD': os.environ.get('DB_PASSWORD', ''),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '3306'),
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                },
            }
        }
else:
    # DESARROLLO LOCAL: SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ================= VALIDACIONES =================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ================= INTERNACIONALIZACIÓN =================
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# ================= ARCHIVOS ESTÁTICOS =================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ================= MEDIA =================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ================= CONFIGURACIÓN ADICIONAL =================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'index'
