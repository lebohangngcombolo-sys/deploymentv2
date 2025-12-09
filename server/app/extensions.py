import cloudinary
import cloudinary.uploader
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_cors import CORS
from pymongo import MongoClient
from authlib.integrations.flask_client import OAuth  # <-- updated
import redis
import firebase_admin
from flask_socketio import SocketIO
from flask_bcrypt import Bcrypt
# In app/extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils.password_validator import PasswordValidator
import os

# ------------------- Flask Extensions -------------------
db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()
oauth = OAuth()  # <-- Authlib OAuth
cors = CORS()
validator = PasswordValidator()   # ← IMPORTANT
bcrypt = Bcrypt()

# ------------------- Cloudinary Client -------------------
class CloudinaryClient:
    def init_app(self, app):
        cloudinary.config(
            cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=app.config['CLOUDINARY_API_KEY'],
            api_secret=app.config['CLOUDINARY_API_SECRET'],
            secure=True
        )

    def upload(self, file_path):
        try:
            return cloudinary.uploader.upload(file_path)
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")

cloudinary_client = CloudinaryClient()

# ------------------- MongoDB Client -------------------
# Use env var for production, fallback to local for dev
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
mongo_db = mongo_client.get_database(os.getenv("MONGO_DB_NAME", "recruitment_cv"))


# ------------------- Rate Limiter -------------------
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]  # optional default rate
)


# ------------------- Redis Client (PRODUCTION SAFE) -------------------
# Uses REDIS_URL if provided (Render/Upstash), else local
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True
)



