from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

db = SQLAlchemy()


def create_app():
    app = Flask(__name__)

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "urban-golf-ba-dev-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
        basedir, "..", "instance", "urbangolf.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    from app.routes.main import main_bp
    from app.routes.player import player_bp
    from app.routes.game import game_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(player_bp, url_prefix="/player")
    app.register_blueprint(game_bp, url_prefix="/game")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    with app.app_context():
        from app import models  # noqa: F401

        db.create_all()

    return app
