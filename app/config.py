import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY            = os.getenv('SECRET_KEY', 'change-me')
    JWT_SECRET_KEY        = os.getenv('JWT_SECRET_KEY', 'jwt-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///brighter_nepal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Tokens expire after 30 days — prevents stale sessions accumulating forever
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_EXPIRY_SECONDS', '2592000'))  # 30 days
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    # SQLAlchemy Connection Pool — tuned for 4 vCPU / 8 GB VPS
    # 4 gevent workers × pool_size(20) = 80 persistent + overflow = 120 max
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size':       int(os.getenv('DB_POOL_SIZE', '20')),
        'max_overflow':    int(os.getenv('DB_MAX_OVERFLOW', '10')),
        'pool_timeout':    int(os.getenv('DB_POOL_TIMEOUT', '30')),
        'pool_recycle':    int(os.getenv('DB_POOL_RECYCLE', '1800')),
        'pool_pre_ping':   True,
    }

    # Response compression — reduces payload sizes by 60-80% for JSON responses
    COMPRESS_ALGORITHM = 'br'       # Brotli (best ratio); falls back to gzip automatically
    COMPRESS_BR_LEVEL  = 4          # Level 4: good balance of speed vs compression
    COMPRESS_MIN_SIZE  = 500        # Only compress responses > 500 bytes

    # Cache Configuration
    USE_REDIS_CACHE = os.getenv('USE_REDIS_CACHE', 'false').lower() == 'true'
    CACHE_TYPE = 'RedisCache' if USE_REDIS_CACHE else 'NullCache'
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '300')) # 5 mins

    GOOGLE_FORMS_CLIENT_ID = os.getenv('GOOGLE_FORMS_CLIENT_ID', '')
    GOOGLE_FORMS_CLIENT_SECRET = os.getenv('GOOGLE_FORMS_CLIENT_SECRET', '')
    GOOGLE_FORMS_CLIENT_SECRET_FILE = os.getenv('GOOGLE_FORMS_CLIENT_SECRET_FILE', '')
    GOOGLE_FORMS_REFRESH_TOKEN = os.getenv('GOOGLE_FORMS_REFRESH_TOKEN', '')
    URL_CIPHER_KEY = os.getenv('URL_CIPHER_KEY', 'bn-url-cipher-v1')
