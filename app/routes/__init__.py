"""Routes package — makes all blueprints importable."""
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
from app.routes.settings     import settings_bp

__all__ = [
    'auth_bp', 'users_bp', 'model_sets_bp', 'weekly_tests_bp',
    'live_classes_bp', 'resources_bp', 'notices_bp',
    'groups_bp', 'payments_bp', 'dashboard_bp',
    'settings_bp',
]
