from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object("config.Config")
    Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .models import User
    from .auth import auth_bp
    from .main import main_bp
    from .trips import trips_bp
    from .admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(trips_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    @app.context_processor
    def inject_helpers():
        from .models import City
        return {"City": City}

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        from flask import render_template
        return render_template("error.html", code=400, message="Security check failed. Please refresh the page and try again."), 400

    @app.errorhandler(413)
    def too_large(_):
        from flask import render_template
        return render_template("error.html", code=413, message="Uploaded file is too large. Maximum size is 5 MB."), 413

    with app.app_context():
        db.create_all()

    return app