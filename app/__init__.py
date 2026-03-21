"""
Flask app factory — registers all extensions and blueprints.
"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

from app.config import Config

db  = SQLAlchemy()
jwt = JWTManager()


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=[app.config['FRONTEND_URL']], supports_credentials=True)

    # Blueprints
    from app.routes.auth         import auth_bp
    from app.routes.users        import users_bp
    from app.routes.model_sets   import model_sets_bp
    from app.routes.weekly_tests import weekly_tests_bp
    from app.routes.live_classes import live_classes_bp
    from app.routes.resources    import resources_bp
    from app.routes.notices      import notices_bp
    from app.routes.groups       import groups_bp
    from app.routes.payments     import payments_bp
    from app.routes.dashboard    import dashboard_bp

    app.register_blueprint(auth_bp,         url_prefix='/api/auth')
    app.register_blueprint(users_bp,        url_prefix='/api/users')
    app.register_blueprint(model_sets_bp,   url_prefix='/api/model-sets')
    app.register_blueprint(weekly_tests_bp, url_prefix='/api/weekly-tests')
    app.register_blueprint(live_classes_bp, url_prefix='/api/live-classes')
    app.register_blueprint(resources_bp,    url_prefix='/api/resources')
    app.register_blueprint(notices_bp,      url_prefix='/api/notices')
    app.register_blueprint(groups_bp,       url_prefix='/api/groups')
    app.register_blueprint(payments_bp,     url_prefix='/api/payments')
    app.register_blueprint(dashboard_bp,    url_prefix='/api/dashboard')

    # Health check
    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '1.0.0'}

    # Create tables on first run
    with app.app_context():
        db.create_all()

    return app
