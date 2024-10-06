import os

CARTOGRAM_EXE = os.environ.get('CARTOGRAM_EXE')
CARTOGRAM_DATA_DIR = os.environ.get('CARTOGRAM_DATA_DIR')
CARTOGRAM_COLOR = os.environ.get('CARTOGRAM_COLOR')
DEBUG = True if os.environ.get('CARTOGRAM_DEBUG').lower() == "true" else False

if "CARTOGRAM_DATABASE_URI" in os.environ: 
    DATABASE_URI = os.environ.get('CARTOGRAM_DATABASE_URI')
    USE_DATABASE = True

    if "POSTGRES_PASSWORD_FILE" in os.environ: 
        f = open(os.environ.get('POSTGRES_PASSWORD_FILE'), "r")
        DATABASE_URI = DATABASE_URI.format(f.read())
else:
    USE_DATABASE = False

HOST = os.environ.get('CARTOGRAM_HOST')
PORT = int(os.environ.get('CARTOGRAM_PORT'))

VERSION = os.environ.get('CARTOGRAM_VERSION')

VITE_SERVER_PORT = os.environ.get('VITE_SERVER_PORT')

SMTP_HOST = os.environ.get('CARTOGRAM_SMTP_HOST')
SMTP_PORT = int(os.environ.get('CARTOGRAM_SMTP_PORT'))
SMTP_AUTHENTICATION_REQUIRED = True if os.environ.get('CARTOGRAM_SMTP_AUTHENTICATION_REQUIRED').lower() == "true" else False
SMTP_USER = os.environ.get('CARTOGRAM_SMTP_USER')
SMTP_PASSWORD = os.environ.get('CARTOGRAM_SMTP_PASSWORD')
SMTP_FROM_EMAIL = os.environ.get('CARTOGRAM_SMTP_FROM_EMAIL')
SMTP_DESTINATION = os.environ.get('CARTOGRAM_SMTP_DESTINATION')

CARTOGRAM_RATE_LIMIT = os.environ.get('CARTOGRAM_RATE_LIMIT')

CARTOGRAM_PROGRESS_SECRET = os.environ.get('CARTOGRAM_PROGRESS_SECRET')
CARTOGRAM_REDIS_HOST = os.environ.get('CARTOGRAM_REDIS_HOST')
CARTOGRAM_REDIS_PORT = int(os.environ.get('CARTOGRAM_REDIS_PORT'))

CARTOGRAM_GA_TRACKING_ID = os.environ.get('CARTOGRAM_GA_TRACKING_ID')

CARTOGRAM_LOCAL_DOCKERIZED = True if os.environ.get('CARTOGRAM_LOCAL_DOCKERIZED').lower() == "true" else False
