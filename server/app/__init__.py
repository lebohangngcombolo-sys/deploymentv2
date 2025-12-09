from flask import Flask
import os
from .extensions import (
    db, jwt, mail, cloudinary_client, mongo_client,
    migrate, cors, bcrypt, oauth, limiter
)
from .models import *
from .routes import auth, admin_routes, candidate_routes, ai_routes, mfa_routes, sso_routes, analytics_routes  # import sso_routes

def create_app():
    app = Flask(__name__)

    # Pick config dynamically
    config_name = os.getenv("FLASK_ENV", "production").capitalize()
    app.config.from_object(f"app.config.{config_name}Config")

    # ---------------- Initialize Extensions ----------------
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)
    oauth.init_app(app)
    bcrypt.init_app(app)
    cloudinary_client.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        origins=["*"],  # adjust for production
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        supports_credentials=True,
    )

    # ---------------- Register Blueprints ----------------
    auth.init_auth_routes(app)  # existing auth routes
    app.register_blueprint(admin_routes.admin_bp, url_prefix="/api/admin")
    app.register_blueprint(candidate_routes.candidate_bp, url_prefix="/api/candidate")
    app.register_blueprint(ai_routes.ai_bp)
    app.register_blueprint(mfa_routes.mfa_bp, url_prefix="/api/auth")  # MFA routes
    app.register_blueprint(analytics_routes.analytics_bp, url_prefix="/api")

    # ---------------- Register SSO Blueprint ----------------
    sso_routes.register_sso_provider(app)      # initialize Auth0 / SSO provider
    app.register_blueprint(sso_routes.sso_bp)  # SSO routes

    # ---------------- Health Check Route ----------------
    @app.route("/api/health")
    def health():
        return {"status": "ok", "message": "Recruitment backend is running!"}, 200

    return app

