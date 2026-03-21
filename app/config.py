import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY            = os.getenv('SECRET_KEY', 'change-me')
    JWT_SECRET_KEY        = os.getenv('JWT_SECRET_KEY', 'jwt-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///brighter_nepal.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
