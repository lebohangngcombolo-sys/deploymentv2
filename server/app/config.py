import os
from datetime import timedelta
from dotenv import load_dotenv

# Load local .env for development
load_dotenv()


class Config:
    """Base configuration."""
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')

    # PostgreSQL
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://user:password@localhost/recruitment_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/recruitment_cv')

    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers", "query_string"]
    JWT_QUERY_STRING_NAME = "access_token"

    # Email / SendGrid defaults
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.sendgrid.net')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', 'apikey')  # 'apikey' literal for SendGrid
    MAIL_PASSWORD = os.getenv('SENDGRID_API_KEY')  # SendGrid API key
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'no-reply@yourdomain.com')

    # OAuth
    GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
    GITHUB_CLIENT_ID = os.getenv('GITHUB_CLIENT_ID')
    GITHUB_CLIENT_SECRET = os.getenv('GITHUB_CLIENT_SECRET')

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')

    # CV Uploads
    CV_UPLOAD_FOLDER = os.getenv('CV_UPLOAD_FOLDER', 'uploads/cvs')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Frontend URL
    FRONTEND_URL = os.getenv('FRONTEND_URL')
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI")
    
    # SSO / Auth0
    SSO_CLIENT_ID = os.getenv('SSO_CLIENT_ID')
    SSO_CLIENT_SECRET = os.getenv('SSO_CLIENT_SECRET')
    SSO_METADATA_URL = os.getenv('SSO_METADATA_URL')
    SSO_USERINFO_URL = os.getenv('SSO_USERINFO_URL')


    
    # SSO Configuration for Company Hub Integration
    SSO_JWT_SECRET = os.getenv('SSO_JWT_SECRET', 'our-super-secret-code-123')  # Same as hub!
    PORTAL_HUB_URL = os.getenv('PORTAL_HUB_URL', 'http://localhost:5001')  # Hub address
    
    


    
class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'apikey'
    SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY')
    MAIL_PASSWORD = SENDGRID_API_KEY
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'lebohangngcombolo@gmail.com')


# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
