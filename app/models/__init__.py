"""SQLAlchemy models — one file per entity group."""
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json, uuid


# ─── Users ────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    plan          = db.Column(db.String(20), default='trial')    # paid | trial
    status        = db.Column(db.String(20), default='active')   # active | suspended
    role          = db.Column(db.String(20), default='student')  # student | admin
    admin_note    = db.Column(db.Text, default='')
    group_id      = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    # Single-device login enforcement
    session_token = db.Column(db.String(64), nullable=True, default=None)  # current valid session
    device_count  = db.Column(db.Integer, default=0)   # total login count across all devices

    def set_password(self, pw: str):    self.password_hash = generate_password_hash(pw)
    def check_password(self, pw: str):  return check_password_hash(self.password_hash, pw)

    def on_login(self) -> str:
        """Rotate session token and increment device_count. Returns new session token."""
        self.session_token = uuid.uuid4().hex
        self.device_count  = (self.device_count or 0) + 1
        return self.session_token

    def to_dict(self, include_email=False):
        d = {
            'id':           self.id,
            'name':         self.name,
            'plan':         self.plan,
            'status':       self.status,
            'role':         self.role,
            'group_id':     self.group_id,
            'device_count': self.device_count or 0,
            'created_at':   self.created_at.isoformat(),
        }
        if include_email:
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
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    attempts    = db.relationship('ModelSetAttempt', backref='model_set', lazy=True)

    def to_dict(self): return {
        'id': self.id, 'title': self.title, 'difficulty': self.difficulty,
        'duration_min': self.duration_min, 'total_questions': self.total_questions,
        'status': self.status, 'targets': json.loads(self.targets) if self.targets else [],
        'created_at': self.created_at.isoformat(),
    }


class ModelSetAttempt(db.Model):
    __tablename__ = 'model_set_attempts'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    model_set_id = db.Column(db.Integer, db.ForeignKey('model_sets.id'), nullable=False)
    score        = db.Column(db.Integer, default=0)
    total        = db.Column(db.Integer, default=100)
    answers      = db.Column(db.Text, default='[]')
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'user_id': self.user_id, 'model_set_id': self.model_set_id,
        'score': self.score, 'total': self.total,
        'completed_at': self.completed_at.isoformat(),
    }


# ─── Weekly Tests ─────────────────────────────────────────────────────────────
class WeeklyTest(db.Model):
    __tablename__ = 'weekly_tests'
    id           = db.Column(db.Integer, primary_key=True)
    title        = db.Column(db.String(200), nullable=False)
    subject      = db.Column(db.String(80), default='General')
    duration_min = db.Column(db.Integer, default=60)
    scheduled_at = db.Column(db.DateTime, nullable=True)
    status       = db.Column(db.String(20), default='scheduled') # live | scheduled | completed
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    questions    = db.relationship('WeeklyTestQuestion', backref='test', lazy=True, cascade='all, delete-orphan')
    attempts     = db.relationship('WeeklyTestAttempt',  backref='test', lazy=True)

    def to_dict(self, include_questions=False):
        d = {
            'id': self.id, 'title': self.title, 'subject': self.subject,
            'duration_min': self.duration_min, 'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'question_count': len(self.questions),
            'created_at': self.created_at.isoformat(),
        }
        if include_questions:
            d['questions'] = [q.to_dict() for q in self.questions]
        return d


class WeeklyTestQuestion(db.Model):
    __tablename__ = 'weekly_test_questions'
    id           = db.Column(db.Integer, primary_key=True)
    test_id      = db.Column(db.Integer, db.ForeignKey('weekly_tests.id'), nullable=False)
    text         = db.Column(db.Text, nullable=False)
    options      = db.Column(db.Text, nullable=False)      # JSON list
    answer_index = db.Column(db.Integer, nullable=False)

    def to_dict(self): return {
        'id': self.id, 'text': self.text,
        'options': json.loads(self.options),
        'answer_index': self.answer_index,
    }


class WeeklyTestAttempt(db.Model):
    __tablename__ = 'weekly_test_attempts'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    test_id      = db.Column(db.Integer, db.ForeignKey('weekly_tests.id'), nullable=False)
    score        = db.Column(db.Integer, default=0)
    total        = db.Column(db.Integer, default=0)
    answers      = db.Column(db.Text, default='[]')
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'user_id': self.user_id, 'test_id': self.test_id,
        'score': self.score, 'total': self.total,
        'submitted_at': self.submitted_at.isoformat(),
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
    watchers     = db.Column(db.Integer, default=0)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    attendance   = db.relationship('LiveClassAttendance', backref='live_class', lazy=True)

    def to_dict(self): return {
        'id': self.id, 'title': self.title, 'teacher': self.teacher,
        'subject': self.subject, 'duration_min': self.duration_min,
        'status': self.status, 'watchers': self.watchers,
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
    id        = db.Column(db.Integer, primary_key=True)
    title     = db.Column(db.String(200), nullable=False)
    subject   = db.Column(db.String(80),  nullable=False)
    format    = db.Column(db.String(20),  nullable=False)  # pdf | video | notes
    section   = db.Column(db.String(80),  default='')      # College Model Questions | Extra Study Materials
    file_url  = db.Column(db.String(500), default='')
    size_label = db.Column(db.String(20), default='')
    downloads  = db.Column(db.Integer, default=0)
    tags      = db.Column(db.Text, default='[]')           # JSON list
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self): return {
        'id': self.id, 'title': self.title, 'subject': self.subject,
        'format': self.format, 'section': self.section,
        'file_url': self.file_url, 'size_label': self.size_label,
        'downloads': self.downloads,
        'tags': json.loads(self.tags) if self.tags else [],
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
    id         = db.Column(db.Integer, primary_key=True)
    group_id   = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    text       = db.Column(db.Text, default='')
    image_url  = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender     = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self): return {
        'id': self.id, 'group_id': self.group_id, 'user_id': self.user_id,
        'sender_name': self.sender.name if self.sender else 'Unknown',
        'text': self.text, 'image_url': self.image_url,
        'created_at': self.created_at.isoformat(),
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
