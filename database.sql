-- BrighterNepal Database Schema (SQLite compatible)
-- Run this to inspect / recreate the schema manually.
-- For seeding use: python app/seed/seed.py

-- Users
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id    TEXT UNIQUE,                 -- random 6-digit ID used for BC login
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    plan          TEXT DEFAULT 'trial',      -- paid | trial
    status        TEXT DEFAULT 'active',     -- active | suspended
    role          TEXT DEFAULT 'student',    -- student | admin
    admin_note    TEXT DEFAULT '',
    group_id      INTEGER REFERENCES groups(id),
    onboarding_completed INTEGER DEFAULT 1,  -- 1 = done, 0 = needs onboarding
    onboarding_data TEXT DEFAULT '{}',       -- saved one-time onboarding form payload (JSON string)
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_users_student_id ON users(student_id);

-- Groups
CREATE TABLE IF NOT EXISTS groups (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    description  TEXT DEFAULT '',
    member_count INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Group messages
CREATE TABLE IF NOT EXISTS group_messages (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id   INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    text       TEXT DEFAULT '',
    image_url  TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Model sets
CREATE TABLE IF NOT EXISTS model_sets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    difficulty      TEXT DEFAULT 'Medium',
    duration_min    INTEGER DEFAULT 120,
    total_questions INTEGER DEFAULT 100,
    status          TEXT DEFAULT 'published',  -- published | draft
    targets         TEXT DEFAULT '["IOE"]',    -- JSON list
    forms_url       TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Model set attempts
CREATE TABLE IF NOT EXISTS model_set_attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    model_set_id INTEGER NOT NULL REFERENCES model_sets(id),
    score        INTEGER DEFAULT 0,
    total        INTEGER DEFAULT 100,
    answers      TEXT DEFAULT '[]',            -- JSON list
    completed_at TEXT DEFAULT (datetime('now'))
);

-- Weekly tests
CREATE TABLE IF NOT EXISTS weekly_tests (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    subject      TEXT DEFAULT 'General',
    duration_min INTEGER DEFAULT 60,
    scheduled_at TEXT,
    status       TEXT DEFAULT 'scheduled',     -- live | scheduled | completed
    forms_url    TEXT DEFAULT '',
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Weekly test questions
CREATE TABLE IF NOT EXISTS weekly_test_questions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id      INTEGER NOT NULL REFERENCES weekly_tests(id) ON DELETE CASCADE,
    text         TEXT NOT NULL,
    options      TEXT NOT NULL,                -- JSON list of 4 options
    answer_index INTEGER NOT NULL
);

-- Weekly test attempts
CREATE TABLE IF NOT EXISTS weekly_test_attempts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL REFERENCES users(id),
    test_id      INTEGER NOT NULL REFERENCES weekly_tests(id),
    score        INTEGER DEFAULT 0,
    total        INTEGER DEFAULT 0,
    answers      TEXT DEFAULT '[]',            -- JSON list
    submitted_at TEXT DEFAULT (datetime('now'))
);

-- Live classes
CREATE TABLE IF NOT EXISTS live_classes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    teacher      TEXT NOT NULL,
    subject      TEXT NOT NULL,
    scheduled_at TEXT,
    duration_min INTEGER DEFAULT 60,
    status       TEXT DEFAULT 'scheduled',     -- live | scheduled | completed | locked
    stream_url   TEXT DEFAULT '',
    group_id     INTEGER,
    watchers     INTEGER DEFAULT 0,
    created_at   TEXT DEFAULT (datetime('now'))
);

-- Live class attendance
CREATE TABLE IF NOT EXISTS live_class_attendance (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    class_id  INTEGER NOT NULL REFERENCES live_classes(id),
    joined_at TEXT DEFAULT (datetime('now'))
);

-- Study resources
CREATE TABLE IF NOT EXISTS resources (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    subject    TEXT NOT NULL,
    format     TEXT DEFAULT 'pdf',             -- pdf | video | notes
    section    TEXT DEFAULT '',                -- College Model Questions | Extra Study Materials | subject name
    file_url   TEXT DEFAULT '',
    size_label TEXT DEFAULT '',
    downloads  INTEGER DEFAULT 0,
    tags       TEXT DEFAULT '[]',             -- JSON list
    created_at TEXT DEFAULT (datetime('now'))
);

-- Notices
CREATE TABLE IF NOT EXISTS notices (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    body       TEXT DEFAULT '',
    category   TEXT DEFAULT 'general',         -- urgent | important | general
    department TEXT DEFAULT '',
    link_url   TEXT DEFAULT '',
    is_pinned  INTEGER DEFAULT 0,              -- 0 = false, 1 = true
    created_at TEXT DEFAULT (datetime('now'))
);

-- Payments
CREATE TABLE IF NOT EXISTS payments (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    amount     REAL NOT NULL,
    method     TEXT DEFAULT 'eSewa',
    status     TEXT DEFAULT 'pending',         -- completed | pending | failed
    created_at TEXT DEFAULT (datetime('now'))
);

-- ── Demo INSERT rows ────────────────────────────────────────────────────────

-- Groups
INSERT INTO groups (name, description, member_count) VALUES
  ('Physics Grade 12 — Elite', 'Official channel for premium curriculum updates.', 300),
  ('Medical Entrance Prep', 'IOM focused preparation group.', 245),
  ('Mathematics Olympiad', 'Advanced maths challenge group.', 180);

-- Admin user (password: admin123)
INSERT INTO users (name, email, password_hash, plan, status, role, group_id) VALUES
  ('Admin User', 'admin@bn.com', 'pbkdf2:sha256:260000$placeholder$hash', 'paid', 'active', 'admin', 1);

-- Students (password: Student@123)
INSERT INTO users (name, email, password_hash, plan, status, role, group_id) VALUES
  ('Aarav Sharma',    'aarav@email.com',   'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 1),
  ('Binita Thapa',    'binita@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 1),
  ('Chirag Adhikari', 'chirag@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'trial', 'active', 'student', 2),
  ('Dipika Rai',      'dipika@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 1),
  ('Elina Gurung',    'elina@email.com',   'pbkdf2:sha256:260000$placeholder$hash', 'trial', 'active', 'student', 3),
  ('Faisal Khan',     'faisal@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 2),
  ('Garima Hamal',    'garima@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 1),
  ('Hari Prasad',     'hari@email.com',    'pbkdf2:sha256:260000$placeholder$hash', 'trial', 'active', 'student', 3),
  ('Ishani Koirala',  'ishani@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 1),
  ('Jayant Bhandari', 'jayant@email.com',  'pbkdf2:sha256:260000$placeholder$hash', 'paid',  'active', 'student', 2);

-- Model Sets
INSERT INTO model_sets (title, difficulty, duration_min, total_questions, status, targets) VALUES
  ('IOE Entrance Mock Set 042',         'Medium', 120, 100, 'published', '["IOE"]'),
  ('Pulchowk Entrance Mock 2024',       'Hard',   120, 100, 'published', '["IOE"]'),
  ('IOE Mock Set 041',                  'Easy',   120, 100, 'published', '["IOE"]'),
  ('IOM Full Syllabus Mock 2024',       'Hard',   180, 150, 'published', '["IOM"]'),
  ('CSIT Entrance Preparation Set',     'Medium',  90,  75, 'published', '["CSIT"]'),
  ('IOE Thermodynamics & Optics',       'Medium', 120, 100, 'draft',     '["IOE"]'),
  ('Biological Sciences Specialization','Hard',   120, 100, 'draft',     '["IOM"]');

-- Notices
INSERT INTO notices (title, body, category, department, link_url, is_pinned) VALUES
  ('End-of-Term Board Exam Schedule Released',        'Download the official PDF starting from Jestha 15.', 'urgent',    'Academic Affairs', '#', 1),
  ('Mandatory Scholarship Orientation for All Students','Session covers application criteria.',              'important', 'Academic Affairs', '#', 1),
  ('Library Extended Hours for Final Exams',          'Library open until 10 PM on weekdays.',              'general',   'Library',          '#', 0),
  ('Chemistry Lab Equipment Return Notice',           'Return all borrowed equipment by Baisakh 30.',       'important', 'Science Dept',     '#', 0),
  ('New Batch Orientation Schedule',                  'Orientation on Falgun 5 at 10 AM.',                  'general',   'Admin',            '#', 0),
  ('IOE 2081 Application Deadline Reminder',          'Last date: Chaitra 20.',                             'urgent',    'Academic Affairs', '#', 0);
