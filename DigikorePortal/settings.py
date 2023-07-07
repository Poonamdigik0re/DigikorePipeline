import os
import ldap
import yaml
from django_auth_ldap.config import LDAPSearch, LDAPSearchUnion
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
# BASE_DIR = "/opt/repos/DigikorePortal"
CONFIG = yaml.load(open(str(BASE_DIR) + '/configs/DigikorePortal.yaml'), Loader=yaml.Loader)
MODELS = yaml.load(open(os.path.join(BASE_DIR, 'configs/models.yaml')), Loader=yaml.Loader)
FOLDERS = yaml.load(open(os.path.join(BASE_DIR, 'configs/folders.yaml')), Loader=yaml.Loader)

# import logging
# logging.basicConfig(format='%(asctime)s : %(levelname)s :  %(message)s',
#                     filename='/tmp/DigikorePortal.log',
#                     level=logging.DEBUG)
#
# LOGGER = logging.getLogger()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = CONFIG['default']['secret_key']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ADMINS = [('Omkar Shinde', 'omkarshinde22@hotmail.com')]
# ALLOWED_HOSTS = CONFIG['default']['allowed_hosts']
ALLOWED_HOSTS = ['*']
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = ['Content-Type']
# Session and CSFR Domain
# CSRF_COOKIE_DOMAIN = 'csrftoken'
# SESSION_COOKIE_DOMAIN = ''
# CSRF_TRUSTED_ORIGINS = ['']



# SSL Configuration
if CONFIG['default']['ssl']:
    HTTPS = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    # SECURE_SSL_REDIRECT = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'base.apps.BaseConfig',
    'corsheaders',
    'DigikorePortal',
    # 'django_celery_results',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'DigikorePortal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'DigikorePortal.wsgi.application'

# Database
# todo: enable DBRouters when deployed in LA
# DATABASE_ROUTERS = ['base.apps.DBRouter']
# CELERY_BROKER_URL = 'redis://127.0.0.1:6379'
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TIMEZONE = 'Asia/Kolkata'
# CELERY_RESULT_BACKEND = 'django-db'


DATABASES = {
        'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'test51',
        'USER': 'root',
        'PASSWORD':'Omkar@123',
        'HOST':'localhost',
        'PORT':'3306',

    }
    # 'slave': {
    #     'ENGINE': 'django.db.backends.mysql',
    #     'NAME': CONFIG['database']['name'],
    #     'HOST': CONFIG['database']['slave_host'],
    #     'PORT': CONFIG['database']['port'],
    #     'USER': CONFIG['database']['user'],
    #     'PASSWORD': CONFIG['database']['password'],
    #     'OPTIONS': {
    #         'sql_mode': 'STRICT_ALL_TABLES',
    #     }
    # },
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Calcutta'
USE_I18N = False
USE_L10N = False
USE_TZ = False


# Static files (CSS, JavaScript, Images)
MEDIA_URL = '/media/'
MEDIA_ROOT = 'media/'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
# STATIC_ROOT = os.path.join(BASE_DIR, 'static/static_root')


AUTHENTICATION_BACKENDS = (
    'django_auth_ldap.backend.LDAPBackend',
    'django.contrib.auth.backends.ModelBackend',
)


AUTH_LDAP_BIND_DN = CONFIG['ldap']['user']
AUTH_LDAP_BIND_PASSWORD = CONFIG['ldap']['password']
AUTH_LDAP_SERVER_URI = f"ldap://{CONFIG['ldap']['server']}"


AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
    LDAPSearch("OU=users,OU=pnq,OU=Legend Sites,DC=legend,DC=work", ldap.SCOPE_SUBTREE, '(sAMAccountName=%(user)s)'),
    LDAPSearch("OU=users,OU=lax,OU=Legend Sites,DC=legend,DC=work", ldap.SCOPE_SUBTREE, '(sAMAccountName=%(user)s)'),
    LDAPSearch("OU=users,OU=yyz,OU=Legend Sites,DC=legend,DC=work", ldap.SCOPE_SUBTREE, '(sAMAccountName=%(user)s)'),
)


AUTH_LDAP_ATTR_MAP = {
    'first_name': 'givenName',
    'last_name': 'sn',
    'email': 'mail',
}
