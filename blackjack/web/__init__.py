import os
from flask import Flask


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates",
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")

    from .routes import bp
    app.register_blueprint(bp)

    return app
