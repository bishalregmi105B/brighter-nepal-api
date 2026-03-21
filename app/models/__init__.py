"""SQLAlchemy models — one file per entity group."""
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json, uuid


# ─── Users ────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'
    id             = db.Column(db.Integer, primary_key=True)
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
        d = {
            'id':           self.id,
            'name':         self.name,
            'plan':         self.plan,
            'status':       self.status,
            'role':         self.role,
            'group_id':     self.group_id,
            'device_count': self.device_count or 0,
            'created_at':   self.created_at.isoformat(),
            'email':        self.email,
        }
        if admin:
            d['whatsapp']       = self.whatsapp
            d['paid_amount']    = self.paid_amount
            d['plain_password'] = self.plain_password
            d['joined_method']  = self.joined_method
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
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    questions   = db.relationship('ModelSetQuestion', backref='model_set', lazy=True, cascade='all, delete-orphan')
    attempts    = db.relationship('ModelSetAttempt', backref='model_set', lazy=True)

    def to_dict(self, include_questions=False):
        d = {
            'id': self.id, 'title': self.title, 'difficulty': self.difficulty,
            'duration_min': self.duration_min, 'total_questions': self.total_questions,
            'status': self.status, 'targets': json.loads(self.targets) if self.targets else [],
            'question_count': len(self.questions),
            'created_at': self.created_at.isoformat(),
        }
        if include_questions:
            d['questions'] = [q.to_dict() for q in self.questions]
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
    forms_url    = db.Column(db.String(500), nullable=True, default=None)  # Google Forms link
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    questions    = db.relationship('WeeklyTestQuestion', backref='test', lazy=True, cascade='all, delete-orphan')
    attempts     = db.relationship('WeeklyTestAttempt',  backref='test', lazy=True)

    def to_dict(self, include_questions=False):
        d = {
            'id': self.id, 'title': self.title, 'subject': self.subject,
            'duration_min': self.duration_min, 'status': self.status,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'question_count': len(self.questions),
            'forms_url': self.forms_url or '',
            'created_at': self.created_at.isoformat(),
        }
        if include_questions:
            d['questions'] = [q.to_dict() for q in self.questions]
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
        'file_url': self.file_url, 'size_label': self.size_label,
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
