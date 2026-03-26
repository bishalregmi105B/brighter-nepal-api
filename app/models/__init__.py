"""SQLAlchemy models — one file per entity group."""
from app import db
from app.utils.url_cipher import encrypt_url
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json, uuid


# ─── Users ────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        # Composite index for the most common admin list query: filter by role + plan/status
        db.Index('ix_users_role_plan',   'role', 'plan'),
        db.Index('ix_users_role_status', 'role', 'status'),
        # For group membership lookups (chat and dashboard)
        db.Index('ix_users_group_id',    'group_id'),
        # For sort-by-date on admin list
        db.Index('ix_users_created_at',  'created_at'),
    )
    id             = db.Column(db.Integer, primary_key=True)
    student_id     = db.Column(db.String(6), unique=True, nullable=True, default=None)  # 6-digit login ID
    name           = db.Column(db.String(120), nullable=False)
    email          = db.Column(db.String(120), unique=True, nullable=False)
    password_hash  = db.Column(db.String(256), nullable=False)
    plain_password = db.Column(db.String(100), nullable=True, default=None)  # stored for admin visibility
    whatsapp       = db.Column(db.String(30), nullable=True, default=None)   # WhatsApp number
    paid_amount    = db.Column(db.Integer, nullable=True, default=None)      # amount paid (NPR)
    joined_method  = db.Column(db.String(200), nullable=True, default=None)  # how contacted (e.g. "WhatsApp referral")
    plan           = db.Column(db.String(20), default='trial')    # paid | trial
    status         = db.Column(db.String(20), default='active')   # active | suspended
    role           = db.Column(db.String(20), default='student')  # student | admin
    admin_note     = db.Column(db.Text, default='')
    group_id       = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    onboarding_completed = db.Column(db.Boolean, default=True)
    onboarding_data = db.Column(db.Text, default='{}')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    # Single-device login enforcement
    session_token  = db.Column(db.String(64), nullable=True, default=None)
    device_count   = db.Column(db.Integer, default=0)

    def set_password(self, pw: str):
        self.password_hash  = generate_password_hash(pw)
        self.plain_password = pw  # keep plain copy for admin
    def check_password(self, pw: str):  return check_password_hash(self.password_hash, pw)

    def on_login(self) -> str:
        """Rotate session token and increment device_count. Returns new session token."""
        self.session_token = uuid.uuid4().hex
        self.device_count  = (self.device_count or 0) + 1
        return self.session_token

    def to_dict(self, include_email=False, admin=False):
        onboarding_data = {}
        if self.onboarding_data:
            try:
                parsed = json.loads(self.onboarding_data)
                onboarding_data = parsed if isinstance(parsed, dict) else {}
            except Exception:
                onboarding_data = {}
        d = {
            'id':           self.id,
            'student_id':   self.student_id or str(self.id).zfill(6),
            'name':         self.name,
            'plan':         self.plan,
            'status':       self.status,
            'role':         self.role,
            'group_id':     self.group_id,
            'onboarding_completed': bool(self.onboarding_completed) if self.onboarding_completed is not None else True,
            'onboarding_data': onboarding_data,
            'device_count': self.device_count or 0,
            'created_at':   self.created_at.isoformat(),
            'email':        self.email,
        }
        if admin:
            joined_method = (self.joined_method or '').strip()
            if not joined_method:
                email = (self.email or '').lower()
                if self.role == 'admin':
                    joined_method = 'Admin Account'
                elif email.endswith('@brighternepal.local') or email.endswith('@placeholder.local'):
                    joined_method = 'Admin Enrollment'
                else:
                    joined_method = 'Legacy Account'
            d['whatsapp']       = self.whatsapp
            d['paid_amount']    = self.paid_amount
            d['plain_password'] = self.plain_password
            d['joined_method']  = joined_method
        elif include_email:
            d['email'] = self.email
        return d


# ─── Model Sets ───────────────────────────────────────────────────────────────
class ModelSet(db.Model):
    __tablename__ = 'model_sets'
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    difficulty  = db.Column(db.String(20), default='Medium')
    duration_min = db.Column(db.Integer, default=120)
    total_questions = db.Column(db.Integer, default=100)
    status      = db.Column(db.String(20), default='published') # published | draft
    targets     = db.Column(db.String(200), default='IOE')      # JSON list stored as string
    forms_url   = db.Column(db.String(500), nullable=True, default=None)  # Optional Google Form link
    google_match_mode = db.Column(db.String(40), default='email_then_student_id')
    google_student_id_question_id = db.Column(db.String(120), nullable=True, default=None)
    google_questions_last_imported_at = db.Column(db.DateTime, nullable=True)
    google_results_last_synced_at = db.Column(db.DateTime, nullable=True)
    google_last_sync_summary = db.Column(db.Text, default='{}')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    questions   = db.relationship('ModelSetQuestion', backref='model_set', lazy=True, cascade='all, delete-orphan')
    attempts    = db.relationship('ModelSetAttempt', backref='model_set', lazy=True)

    def to_dict(self, include_questions=False, include_google=False):
        d = {
            'id': self.id, 'title': self.title, 'difficulty': self.difficulty,
            'duration_min': self.duration_min, 'total_questions': self.total_questions,
            'status': self.status, 'targets': json.loads(self.targets) if self.targets else [],
            'forms_url': self.forms_url or '',
            'google_match_mode': self.google_match_mode or 'email_then_student_id',
            'google_student_id_question_id': self.google_student_id_question_id,
            'google_questions_last_imported_at': self.google_questions_last_imported_at.isoformat() if self.google_questions_last_imported_at else None,
            'google_results_last_synced_at': self.google_results_last_synced_at.isoformat() if self.google_results_last_synced_at else None,
            'google_last_sync_summary': json.loads(self.google_last_sync_summary) if self.google_last_sync_summary else {},
            'question_count': len(self.questions),
            'created_at': self.created_at.isoformat(),
        }
        if include_questions:
            d['questions'] = [q.to_dict() for q in self.questions]
        if include_google:
            d['google_questions'] = [
                q.to_dict()
                for q in GoogleFormQuestionMap.query.filter_by(entity_type='model_set', entity_id=self.id)
                .order_by(GoogleFormQuestionMap.order_index.asc())
                .all()
            ]
        return d

class Question(db.Model):
    __tablename__ = 'questions'
    id           = db.Column(db.Integer, primary_key=True)
    subject      = db.Column(db.String(80), default='General')
    text         = db.Column(db.Text, nullable=False)
    options      = db.Column(db.Text, nullable=False)      # JSON list
    answer_index = db.Column(db.Integer, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'subject': self.subject, 'text': self.text,
        'options': json.loads(self.options),
        'answer_index': self.answer_index,
    }


class ModelSetQuestion(db.Model):
    __tablename__ = 'model_set_questions'
    id           = db.Column(db.Integer, primary_key=True)
    model_set_id = db.Column(db.Integer, db.ForeignKey('model_sets.id'), nullable=False)
    question_id  = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    order_index  = db.Column(db.Integer, default=0)
    
    question     = db.relationship('Question', lazy='joined')

    def to_dict(self):
        # Merge question data to match the old schema output perfectly for the frontend
        d = self.question.to_dict()
        d['link_id'] = self.id
        return d


class ModelSetAttempt(db.Model):
    __tablename__ = 'model_set_attempts'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_set_id = db.Column(db.Integer, db.ForeignKey('model_sets.id'), nullable=False)
    score        = db.Column(db.Integer, default=0)
    total        = db.Column(db.Integer, default=100)
    answers      = db.Column(db.Text, default='[]')
    source       = db.Column(db.String(30), default='internal')
    external_response_id = db.Column(db.String(120), nullable=True, default=None)
    matched_by   = db.Column(db.String(40), nullable=True, default=None)
    review_payload = db.Column(db.Text, default='[]')
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    user         = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self, include_review=False): 
        d = {
            'id': self.id, 'user_id': self.user_id, 'model_set_id': self.model_set_id,
            'score': self.score, 'total': self.total,
            'source': self.source or 'internal',
            'external_response_id': self.external_response_id,
            'matched_by': self.matched_by,
            'completed_at': self.completed_at.isoformat(),
            'user_name': self.user.name if self.user else '',
            'student_id': self.user.student_id if self.user else None,
            'email': self.user.email if self.user else '',
        }
        if include_review:
            d['review_payload'] = json.loads(self.review_payload) if self.review_payload else []
        return d


# ─── Weekly Tests ─────────────────────────────────────────────────────────────
class WeeklyTest(db.Model):
    __tablename__ = 'weekly_tests'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    subject      = db.Column(db.String(80), default='General')
    duration_min = db.Column(db.Integer, default=60)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default='scheduled') # live | scheduled | completed
    forms_url    = db.Column(db.String(500), nullable=True, default=None)  # Google Forms link
    google_match_mode = db.Column(db.String(40), default='email_then_student_id')
    google_student_id_question_id = db.Column(db.String(120), nullable=True, default=None)
    google_questions_last_imported_at = db.Column(db.DateTime, nullable=True)
    google_results_last_synced_at = db.Column(db.DateTime, nullable=True)
    google_last_sync_summary = db.Column(db.Text, default='{}')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    questions    = db.relationship('WeeklyTestQuestion', backref='test', lazy=True, cascade='all, delete-orphan')
    attempts     = db.relationship('WeeklyTestAttempt',  backref='test', lazy=True)

    def to_dict(self, include_questions=False, include_google=False):
        d = {
            'id': self.id, 'title': self.title, 'subject': self.subject,
            'duration_min': self.duration_min, 'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'question_count': len(self.questions),
            'total_questions': len(self.questions),
            'forms_url': self.forms_url or '',
            'google_match_mode': self.google_match_mode or 'email_then_student_id',
            'google_student_id_question_id': self.google_student_id_question_id,
            'google_questions_last_imported_at': self.google_questions_last_imported_at.isoformat() if self.google_questions_last_imported_at else None,
            'google_results_last_synced_at': self.google_results_last_synced_at.isoformat() if self.google_results_last_synced_at else None,
            'google_last_sync_summary': json.loads(self.google_last_sync_summary) if self.google_last_sync_summary else {},
            'created_at': self.created_at.isoformat(),
        }
        if include_questions:
            d['questions'] = [q.to_dict() for q in self.questions]
        if include_google:
            d['google_questions'] = [
                q.to_dict()
                for q in GoogleFormQuestionMap.query.filter_by(entity_type='weekly_test', entity_id=self.id)
                .order_by(GoogleFormQuestionMap.order_index.asc())
                .all()
            ]
        return d


class WeeklyTestQuestion(db.Model):
    __tablename__ = 'weekly_test_questions'
    id           = db.Column(db.Integer, primary_key=True)
    test_id      = db.Column(db.Integer, db.ForeignKey('weekly_tests.id'), nullable=False)
    question_id  = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    order_index  = db.Column(db.Integer, default=0)

    question     = db.relationship('Question', lazy='joined')

    def to_dict(self):
        # Merge question data to match the old schema output perfectly for the frontend
        d = self.question.to_dict()
        d['link_id'] = self.id
        return d


class WeeklyTestAttempt(db.Model):
    __tablename__ = 'weekly_test_attempts'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id      = db.Column(db.Integer, db.ForeignKey('weekly_tests.id'), nullable=False)
    score        = db.Column(db.Integer, default=0)
    total        = db.Column(db.Integer, default=0)
    answers      = db.Column(db.Text, default='[]')
    source       = db.Column(db.String(30), default='internal')
    external_response_id = db.Column(db.String(120), nullable=True, default=None)
    matched_by   = db.Column(db.String(40), nullable=True, default=None)
    review_payload = db.Column(db.Text, default='[]')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    user         = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self, include_review=False): 
        d = {
            'id': self.id, 'user_id': self.user_id, 'test_id': self.test_id,
            'score': self.score, 'total': self.total,
            'source': self.source or 'internal',
            'external_response_id': self.external_response_id,
            'matched_by': self.matched_by,
            'submitted_at': self.submitted_at.isoformat(),
            'user_name': self.user.name if self.user else '',
            'student_id': self.user.student_id if self.user else None,
            'email': self.user.email if self.user else '',
        }
        if include_review:
            d['review_payload'] = json.loads(self.review_payload) if self.review_payload else []
        return d


class GoogleFormQuestionMap(db.Model):
    __tablename__ = 'google_form_question_maps'
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'google_question_id', name='uq_google_form_question_maps_entity_question'),
        db.Index('ix_google_form_question_maps_entity_order', 'entity_type', 'entity_id', 'order_index'),
    )
    id               = db.Column(db.Integer, primary_key=True)
    entity_type      = db.Column(db.String(30), nullable=False)   # model_set | weekly_test
    entity_id        = db.Column(db.Integer, nullable=False)
    google_question_id = db.Column(db.String(120), nullable=False)
    title            = db.Column(db.String(500), default='')
    description      = db.Column(db.Text, default='')
    question_type    = db.Column(db.String(80), default='unknown')
    choice_type      = db.Column(db.String(40), default='')
    options_json     = db.Column(db.Text, default='[]')
    correct_answer   = db.Column(db.String(500), default='')
    point_value      = db.Column(db.Integer, default=1)
    order_index      = db.Column(db.Integer, default=0)
    local_question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    is_supported     = db.Column(db.Boolean, default=False)
    is_imported      = db.Column(db.Boolean, default=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    local_question   = db.relationship('Question', foreign_keys=[local_question_id])

    def to_dict(self): return {
        'id': self.id,
        'entity_type': self.entity_type,
        'entity_id': self.entity_id,
        'google_question_id': self.google_question_id,
        'title': self.title,
        'description': self.description,
        'question_type': self.question_type,
        'choice_type': self.choice_type,
        'options': json.loads(self.options_json) if self.options_json else [],
        'correct_answer': self.correct_answer or '',
        'point_value': self.point_value or 0,
        'order_index': self.order_index,
        'local_question_id': self.local_question_id,
        'is_supported': bool(self.is_supported),
        'is_imported': bool(self.is_imported),
    }


class GoogleFormResponseSyncLog(db.Model):
    __tablename__ = 'google_form_response_sync_logs'
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'external_response_id', name='uq_google_form_response_sync_logs_entity_response'),
        db.Index('ix_google_form_response_sync_logs_entity_status', 'entity_type', 'entity_id', 'status'),
    )
    id               = db.Column(db.Integer, primary_key=True)
    entity_type      = db.Column(db.String(30), nullable=False)   # model_set | weekly_test
    entity_id        = db.Column(db.Integer, nullable=False)
    external_response_id = db.Column(db.String(120), nullable=False)
    respondent_email = db.Column(db.String(200), default='')
    student_id_value = db.Column(db.String(120), default='')
    matched_user_id  = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    matched_by       = db.Column(db.String(40), nullable=True, default=None)
    status           = db.Column(db.String(30), default='unmatched')
    score            = db.Column(db.Integer, default=0)
    total            = db.Column(db.Integer, default=0)
    submitted_at     = db.Column(db.DateTime, nullable=True)
    payload_json     = db.Column(db.Text, default='{}')
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at       = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    matched_user     = db.relationship('User', foreign_keys=[matched_user_id])

    def to_dict(self): return {
        'id': self.id,
        'entity_type': self.entity_type,
        'entity_id': self.entity_id,
        'external_response_id': self.external_response_id,
        'respondent_email': self.respondent_email or '',
        'student_id_value': self.student_id_value or '',
        'matched_user_id': self.matched_user_id,
        'matched_by': self.matched_by,
        'status': self.status,
        'score': self.score,
        'total': self.total,
        'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
        'payload': json.loads(self.payload_json) if self.payload_json else {},
    }


# ─── Live Classes ─────────────────────────────────────────────────────────────
class LiveClass(db.Model):
    __tablename__ = 'live_classes'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    teacher      = db.Column(db.String(120), nullable=False)
    subject      = db.Column(db.String(80),  nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    duration_min = db.Column(db.Integer, default=60)
    status       = db.Column(db.String(20), default='scheduled') # live | scheduled | completed | locked
    stream_url   = db.Column(db.String(500), default='')
    group_id     = db.Column(db.Integer, nullable=True)
    watchers     = db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    attendance   = db.relationship('LiveClassAttendance', backref='live_class', lazy=True)

    def to_dict(self): return {
        'id': self.id, 'title': self.title, 'teacher': self.teacher,
        'subject': self.subject, 'duration_min': self.duration_min,
        'status': self.status, 'watchers': self.watchers,
        'stream_url': encrypt_url(self.stream_url),
        'group_id': self.group_id,
        'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
        'created_at': self.created_at.isoformat(),
    }


class LiveClassAttendance(db.Model):
    __tablename__ = 'live_class_attendance'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id   = db.Column(db.Integer, db.ForeignKey('live_classes.id'), nullable=False)
    joined_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ─── Resources ────────────────────────────────────────────────────────────────
class Resource(db.Model):
    __tablename__ = 'resources'
    id            = db.Column(db.Integer, primary_key=True)
    title         = db.Column(db.String(200), nullable=False)
    subject       = db.Column(db.String(80),  nullable=False)
    format        = db.Column(db.String(20),  nullable=False)  # pdf | video | link | notes | file
    section       = db.Column(db.String(80),  default='')      # College Model Questions | Extra Study Materials
    file_url      = db.Column(db.String(500), default='')      # URL: PDF URL / YouTube URL / website URL / file URL
    size_label    = db.Column(db.String(20),  default='')
    downloads     = db.Column(db.Integer,     default=0)
    tags          = db.Column(db.Text,        default='[]')    # JSON list
    description   = db.Column(db.Text,        default='')     # Rich text description
    thumbnail_url = db.Column(db.String(500), default='')     # Optional cover image URL
    live_class_id = db.Column(db.Integer, db.ForeignKey('live_classes.id'), nullable=True, default=None)
    created_at    = db.Column(db.DateTime,   default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'title': self.title, 'subject': self.subject,
        'format': self.format, 'section': self.section,
        'file_url': encrypt_url(self.file_url), 'size_label': self.size_label,
        'downloads': self.downloads,
        'tags': json.loads(self.tags) if self.tags else [],
        'description': self.description or '',
        'thumbnail_url': self.thumbnail_url or '',
        'live_class_id': self.live_class_id,
        'created_at': self.created_at.isoformat(),
    }


# ─── Notices ──────────────────────────────────────────────────────────────────
class Notice(db.Model):
    __tablename__ = 'notices'
    id         = db.Column(db.Integer, primary_key=True)
    title      = db.Column(db.String(300), nullable=False)
    body       = db.Column(db.Text, default='')
    category   = db.Column(db.String(30), default='general') # urgent | important | general
    department = db.Column(db.String(100), default='')
    link_url   = db.Column(db.String(500), default='')
    is_pinned  = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'title': self.title, 'body': self.body,
        'category': self.category, 'department': self.department,
        'link_url': self.link_url, 'is_pinned': self.is_pinned,
        'created_at': self.created_at.isoformat(),
    }


# ─── Platform Settings ────────────────────────────────────────────────────────
class PlatformSetting(db.Model):
    __tablename__ = 'platform_settings'
    id         = db.Column(db.Integer, primary_key=True)
    key        = db.Column(db.String(120), unique=True, nullable=False)
    value      = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value or '',
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


# ─── Groups & Messages ────────────────────────────────────────────────────────
class Group(db.Model):
    __tablename__  = 'groups'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    member_count = db.Column(db.Integer, default=0)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    members     = db.relationship('User',         backref='group',    lazy=True, foreign_keys='User.group_id')
    messages    = db.relationship('GroupMessage', backref='group',    lazy=True, cascade='all, delete-orphan')

    def to_dict(self): return {
        'id': self.id, 'name': self.name, 'description': self.description,
        'member_count': self.member_count, 'created_at': self.created_at.isoformat(),
    }


class GroupMessage(db.Model):
    __tablename__ = 'group_messages'
    __table_args__ = (
        db.Index('ix_group_messages_group_created', 'group_id', 'created_at'),
    )
    id         = db.Column(db.Integer, primary_key=True)
    group_id   = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    text       = db.Column(db.Text, default='')
    image_url  = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender     = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self): return {
        'id': self.id, 'group_id': self.group_id, 'user_id': self.user_id,
        'sender_name': self.sender.name if self.sender else 'Unknown',
        'text': self.text, 'image_url': self.image_url,
        'created_at': self.created_at.isoformat(),
    }


class LiveClassMessage(db.Model):
    """Chat messages specific to a live class session."""
    __tablename__ = 'live_class_messages'
    __table_args__ = (
        db.Index('ix_lc_messages_class_created', 'class_id', 'created_at'),
    )
    id           = db.Column(db.Integer, primary_key=True)
    class_id     = db.Column(db.Integer, db.ForeignKey('live_classes.id'), nullable=False)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text         = db.Column(db.Text, default='')
    image_url    = db.Column(db.Text, nullable=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    sender       = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self): return {
        'id':          self.id,
        'class_id':    self.class_id,
        'user_id':     self.user_id,
        'sender_name': self.sender.name if self.sender else 'Unknown',
        'text':        self.text,
        'image_url':   self.image_url,
        'created_at':  self.created_at.isoformat(),
    }


# ─── Payments ─────────────────────────────────────────────────────────────────
class Payment(db.Model):
    __tablename__ = 'payments'
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount     = db.Column(db.Float,   nullable=False)
    method     = db.Column(db.String(50), default='eSewa')
    status     = db.Column(db.String(20), default='pending')  # completed | pending | failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user       = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self): return {
        'id': self.id, 'user_id': self.user_id,
        'user_name': self.user.name if self.user else '',
        'amount': self.amount, 'method': self.method, 'status': self.status,
        'created_at': self.created_at.isoformat(),
    }


# ─── Contact Methods (admin-configurable dropdown options for joined_method) ─────
class ContactMethod(db.Model):
    __tablename__ = 'contact_methods'
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)   # e.g. "WhatsApp 1", "Messenger 1"
    channel   = db.Column(db.String(30),  default='other')  # whatsapp | messenger | facebook | other
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'name': self.name,
        'channel': self.channel, 'is_active': self.is_active,
    }
