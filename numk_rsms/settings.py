from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'change-this-in-production')
DEBUG = os.getenv('DEBUG', '0') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','core']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'numk_rsms.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[BASE_DIR/'core'/'templates'],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'numk_rsms.wsgi.application'
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('POSTGRES_DB','numk_rsms'),'USER':os.getenv('POSTGRES_USER','numk_rsms'),'PASSWORD':os.getenv('POSTGRES_PASSWORD','change-me'),'HOST':os.getenv('POSTGRES_HOST','localhost'),'PORT':os.getenv('POSTGRES_PORT','5432')}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE='en-us'; TIME_ZONE=os.getenv('TIME_ZONE','Africa/Lagos'); USE_I18N=True; USE_TZ=True
STATIC_URL='static/'; DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'; LOGIN_URL='/login/'; LOGIN_REDIRECT_URL='/'; LOGOUT_REDIRECT_URL='/login/'
