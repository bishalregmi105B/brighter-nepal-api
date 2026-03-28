"""
Add initial users to the production database.
Run: python add_users.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import User

app = create_app()

USERS = [
    {
        'name':  'Brighter Nepal Admin',
        'email': 'admin@brighternepal.edu.np',
        'password': 'BrighterAdmin@2081',
        'role': 'admin',
        'plan': 'paid',
        'joined_method': 'Admin Account',
        'onboarding_completed': True,
    },
    {
        'name':  'Aashish Maharjan',
        'email': 'aashish.maharjan@gmail.com',
        'password': 'Student@2081',
        'role': 'student',
        'plan': 'trial',
        'joined_method': 'Direct Signup',
        'onboarding_completed': False,
    },
]

with app.app_context():
    for u in USERS:
        if User.query.filter_by(email=u['email']).first():
            print(f"[skip] {u['email']} already exists")
            continue
        user = User(
            name=u['name'],
            email=u['email'],
            role=u['role'],
            plan=u['plan'],
            joined_method=u['joined_method'],
            onboarding_completed=u['onboarding_completed'],
        )
        user.set_password(u['password'])
        db.session.add(user)
        print(f"[add]  {u['email']} ({u['role']})")

    db.session.commit()
    print("Done.")
