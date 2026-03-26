"""Helpers for generating unique 6-digit student IDs."""
import random
from app.models import User

_rng = random.SystemRandom()


def generate_unique_student_id() -> str:
    """Return a unique 6-digit numeric student ID as a string."""
    for _ in range(500):
        sid = f'{_rng.randint(0, 999999):06d}'
        if not User.query.filter_by(student_id=sid).first():
            return sid

    # Extremely unlikely fallback path.
    for i in range(1_000_000):
        sid = f'{i:06d}'
        if not User.query.filter_by(student_id=sid).first():
            return sid

    raise RuntimeError('No available student IDs left')
