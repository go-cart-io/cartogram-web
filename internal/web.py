#!/usr/bin/env python
import logging
import os

import settings
from asset import Asset
from database import db
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.middleware.proxy_fix import ProxyFix


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
    Asset(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    app.app_context().push()
    app.logger.setLevel(logging.INFO)
    app.secret_key = settings.SECRET_KEY
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.DATABASE_URI
    # This gets rid of an annoying Flask error message. We don't need this feature anyway.
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["ENV"] = "development" if settings.IS_DEBUG else "production"
    app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB
    app.config["MAX_FORM_MEMORY_SIZE"] = 100 * 1024 * 1024

    if settings.USE_DATABASE:
        db.init_app(app)
        Migrate(app, db)

    try:
        with open(
            os.path.join(os.path.dirname(__file__), "executable/release-tag.txt")
        ) as f:
            app.config["CPP_VERSION"] = " v" + f.read().strip()
        with open(os.path.join(os.path.dirname(__file__), "version.txt")) as f:
            app.config["VERSION"] = " v" + f.read().strip()
    except FileNotFoundError:
        pass

    from routes.api_routes import api_bp
    from routes.cartogram_routes import cartogram_bp
    from routes.main_routes import main_bp
    from routes.maintenance_routes import maintenance_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(cartogram_bp)
    app.register_blueprint(maintenance_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host=settings.HOST, port=settings.PORT)
