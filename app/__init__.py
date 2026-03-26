"""
Flask app factory — registers all extensions and blueprints.
"""
from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_compress import Compress
from sqlalchemy import inspect, text, or_

from app.config import Config

db       = SQLAlchemy()
jwt      = JWTManager()
cache    = Cache()
compress = Compress()
limiter  = Limiter(
    key_func=get_remote_address,
    default_limits=[],           # no global limit — apply per-route only
    storage_uri=None,            # set dynamically in create_app based on USE_REDIS_CACHE
)

def _ensure_legacy_columns(app: Flask) -> None:
    """
    Add newly introduced nullable columns for older SQLite DBs that were
    created before these fields existed.
    """
    required_columns: dict[str, dict[str, str]] = {
        'users': {
            'student_id': 'TEXT',
            'onboarding_completed': 'INTEGER DEFAULT 1',
            'onboarding_data': "TEXT DEFAULT '{}'",
        },
        'model_sets': {
            'forms_url': 'TEXT',
            'forms_view_url': 'TEXT',
            "google_match_mode": "TEXT DEFAULT 'email_then_student_id'",
            'google_student_id_question_id': 'TEXT',
            'google_questions_last_imported_at': 'DATETIME',
            'google_results_last_synced_at': 'DATETIME',
            "google_last_sync_summary": "TEXT DEFAULT '{}'",
        },
        'weekly_tests': {
            'forms_url': 'TEXT',
            'forms_view_url': 'TEXT',
            "google_match_mode": "TEXT DEFAULT 'email_then_student_id'",
            'google_student_id_question_id': 'TEXT',
            'google_questions_last_imported_at': 'DATETIME',
            'google_results_last_synced_at': 'DATETIME',
            "google_last_sync_summary": "TEXT DEFAULT '{}'",
        },
        'model_set_attempts': {
            "source": "TEXT DEFAULT 'internal'",
            'external_response_id': 'TEXT',
            'matched_by': 'TEXT',
            "review_payload": "TEXT DEFAULT '[]'",
        },
        'weekly_test_attempts': {
            "source": "TEXT DEFAULT 'internal'",
            'external_response_id': 'TEXT',
            'matched_by': 'TEXT',
            "review_payload": "TEXT DEFAULT '[]'",
        },
        'live_classes': {
            'stream_url': 'TEXT',
            'group_id': 'INTEGER',
        },
    }

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    with db.engine.begin() as conn:
        for table_name, cols in required_columns.items():
            if table_name not in table_names:
                continue
            existing = {c['name'] for c in inspector.get_columns(table_name)}
            for col_name, col_type in cols.items():
                if col_name in existing:
                    continue
                try:
                    conn.execute(text(f'ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type}'))
                    app.logger.info('Added missing column %s.%s', table_name, col_name)
                except Exception as err:
                    app.logger.warning('Could not add missing column %s.%s (%s)', table_name, col_name, err)
        try:
            conn.execute(text('CREATE UNIQUE INDEX IF NOT EXISTS ix_users_student_id ON users(student_id)'))
        except Exception as err:
            app.logger.warning('Could not ensure index ix_users_student_id (%s)', err)
        try:
            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_model_set_attempts_external_response_id ON model_set_attempts(external_response_id)'))
            conn.execute(text('CREATE INDEX IF NOT EXISTS ix_weekly_test_attempts_external_response_id ON weekly_test_attempts(external_response_id)'))
        except Exception as err:
            app.logger.warning('Could not ensure Google attempt indexes (%s)', err)

def _ensure_user_defaults(app: Flask) -> None:
    """
    Backfill user metadata for older DB rows so admin UI fields are never blank:
    - ensure student_id exists for every user
    - ensure joined_method is populated
    - ensure onboarding_completed is non-null
    - seed default contact methods when table is empty/new
    """
    from app.models import User, ContactMethod
    from app.utils.student_id import generate_unique_student_id

    changed = False

    users_missing_sid = User.query.filter(
        or_(User.student_id.is_(None), db.func.trim(User.student_id) == '')
    ).all()
    for user in users_missing_sid:
        user.student_id = generate_unique_student_id()
        changed = True

    users_missing_joined = User.query.filter(
        or_(User.joined_method.is_(None), db.func.trim(User.joined_method) == '')
    ).all()
    for user in users_missing_joined:
        email = (user.email or '').lower()
        if user.role == 'admin':
            user.joined_method = 'Admin Account'
        elif email.endswith('@brighternepal.local') or email.endswith('@placeholder.local'):
            user.joined_method = 'Admin Enrollment'
        else:
            user.joined_method = 'Legacy Account'
        changed = True

    users_missing_onboarding = User.query.filter(User.onboarding_completed.is_(None)).all()
    for user in users_missing_onboarding:
        user.onboarding_completed = True
        changed = True
    users_missing_onboarding_data = User.query.filter(
        or_(User.onboarding_data.is_(None), db.func.trim(User.onboarding_data) == '')
    ).all()
    for user in users_missing_onboarding_data:
        user.onboarding_data = '{}'
        changed = True

    default_methods = [
        ('Admin Enrollment', 'other'),
        ('Self Signup', 'other'),
        ('Legacy Account', 'other'),
        ('WhatsApp', 'whatsapp'),
        ('Messenger', 'messenger'),
        ('Facebook', 'facebook'),
        ('Search Engine', 'other'),
        ('Friend / Recommendation', 'other'),
    ]
    existing = {(m.name or '').strip().lower() for m in ContactMethod.query.all()}
    for name, channel in default_methods:
        if name.lower() in existing:
            continue
        db.session.add(ContactMethod(name=name, channel=channel, is_active=True))
        changed = True

    if changed:
        db.session.commit()
        app.logger.info('Backfilled user/contact defaults for legacy rows')


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    compress.init_app(app)
    # Wire limiter with Redis backend when available for distributed rate limiting
    use_redis = app.config.get('USE_REDIS_CACHE', False)
    redis_url = app.config.get('CACHE_REDIS_URL', 'redis://localhost:6379/0')
    limiter._storage_uri = f'{redis_url}' if use_redis else 'memory://'
    limiter.init_app(app)
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
    from app.routes.subjects     import subjects_bp
    from app.routes.settings     import settings_bp

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
    app.register_blueprint(subjects_bp,     url_prefix='/api/subjects')
    app.register_blueprint(settings_bp,     url_prefix='/api/settings')

    # Health check
    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'version': '1.0.0'}

    # Create tables on first run
    with app.app_context():
        db.create_all()
        _ensure_legacy_columns(app)
        try:
            _ensure_user_defaults(app)
        except Exception as err:
            db.session.rollback()
            app.logger.warning('Could not backfill user defaults (%s)', err)

    return app
