import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY            = os.getenv('SECRET_KEY', 'change-me')
    JWT_SECRET_KEY        = os.getenv('JWT_SECRET_KEY', 'jwt-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///brighter_nepal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = False  # Changed from 604800 (7 days) for practically infinite duration
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    # SQLAlchemy Connection Pool — critical for MySQL under load
    # Without this, SQLAlchemy defaults to 5 connections (instantly saturated under load)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size':       int(os.getenv('DB_POOL_SIZE', '30')),      # 30 persistent connections
        'max_overflow':    int(os.getenv('DB_MAX_OVERFLOW', '60')),   # 60 burst connections = 90 max total
        'pool_timeout':    int(os.getenv('DB_POOL_TIMEOUT', '30')),   # wait up to 30s for a free connection
        'pool_recycle':    int(os.getenv('DB_POOL_RECYCLE', '1800')), # recycle connections every 30 min
        'pool_pre_ping':   True,  # ping before reuse – detects stale/dropped connections
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
