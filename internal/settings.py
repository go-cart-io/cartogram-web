import os

VITE_SERVER_PORT = os.environ.get("VITE_SERVER_PORT")

HOST = os.environ.get("CARTOGRAM_HOST", "0.0.0.0")
PORT = int(os.environ.get("CARTOGRAM_PORT", "5000"))
IS_DEBUG = os.environ.get("FLASK_DEBUG", False)

SECRET_KEY = os.environ.get("CARTOGRAM_SECRET_KEY", "")
if not SECRET_KEY or SECRET_KEY == "":
    SECRET_KEY = "LTTNWg8luqfWKfDxjFaeC3vYoGrC2r2f5mtXo5IE/jt1GcY7/JaSq8V/tB"

CARTOGRAM_RATE_LIMIT = os.environ.get("CARTOGRAM_RATE_LIMIT", "100 per hour")

if "CARTOGRAM_DATABASE_URI" in os.environ:
    DATABASE_URI = os.environ.get("CARTOGRAM_DATABASE_URI", None)
    USE_DATABASE = True
    POSTGRES_PASSWORD_FILE = os.environ.get("POSTGRES_PASSWORD_FILE", None)

    if DATABASE_URI and POSTGRES_PASSWORD_FILE:
        f = open(POSTGRES_PASSWORD_FILE, "r")
        DATABASE_URI = DATABASE_URI.format(f.read())
else:
    USE_DATABASE = False

CARTOGRAM_REDIS_HOST = os.environ.get("CARTOGRAM_REDIS_HOST", "redis")
CARTOGRAM_REDIS_PORT = int(os.environ.get("CARTOGRAM_REDIS_PORT", 6379))

SMTP_HOST = os.environ.get("CARTOGRAM_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("CARTOGRAM_SMTP_PORT", 2525))
SMTP_AUTHENTICATION_REQUIRED = (
    os.environ.get("CARTOGRAM_SMTP_AUTHENTICATION_REQUIRED", "false").lower() == "true"
)
SMTP_USER = os.environ.get("CARTOGRAM_SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("CARTOGRAM_SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.environ.get("CARTOGRAM_SMTP_FROM_EMAIL", "")
SMTP_DESTINATION = os.environ.get("CARTOGRAM_SMTP_DESTINATION", "")

CARTOGRAM_GA_TRACKING_ID = os.environ.get("CARTOGRAM_GA_TRACKING_ID", "")
