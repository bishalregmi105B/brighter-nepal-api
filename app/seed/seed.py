"""
Seed script — Brighter Nepal BridgeCourse Preparation Institute
Focus: +2 Science / Management / A-Level / Humanities / CTEVT Bridge Courses ONLY.
Real resource links from studynotesnepal.com & edusanjal.com.
Large question bank (145 Qs) across all subjects.
Run: python app/seed/seed.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app, db
from app.models import (
    User, Group, ModelSet, ModelSetQuestion, WeeklyTest, WeeklyTestQuestion,
    Question, LiveClass, Resource, Notice, Payment, GroupMessage
)
from datetime import datetime, timedelta
import json

app = create_app()


# ─────────────────────────────────────────────────────────────────────────────
# REAL RESOURCE LINKS (all publicly accessible, no login required)
# ─────────────────────────────────────────────────────────────────────────────
REAL_LINKS = {
    # StudyNotesNepal — subject-wise Bridge Course notes pages
    'physics_bridge':    'https://studynotesnepal.com/physics-bridge-course-after-see-entrance-preparation/',
    'math_bridge':       'https://studynotesnepal.com/math-bridge-course-after-see-entrance-preparation/',
    'chemistry_bridge':  'https://studynotesnepal.com/chemistry-bridge-course-after-see-entrance-preparation/',
    'english_bridge':    'https://studynotesnepal.com/english-bridge-course-after-see-entrance-preparation/',
    'zoology_bridge':    'https://studynotesnepal.com/zoology-bridge-course-after-see-entrance-preparation/',
    'botany_bridge':     'https://studynotesnepal.com/botany-bridge-course-after-see-entrance-preparation/',
    'ecology_bridge':    'https://studynotesnepal.com/ecology-bridge-course-after-see-entrance-preparation/',
    # StudyNotesNepal — MCQ model question pages
    'model_q':           'https://studynotesnepal.com/after-see-model-questions/',
    'top_college_q':     'https://studynotesnepal.com/see-entrance-model-question/',
    'practice_set1':     'https://studynotesnepal.com/st-xavier-based-practice-model-question/',
    # Edusanjal — free PDF and online course
    'edusanjal_book':    'https://media.edusanjal.com/brochure/Post-_SEE_students_GEARING_UP_for_2_Entrance_Exams_Book.pdf',
    'edusanjal_course':  'https://learn.edusanjal.com/bridge-course',
    'edusanjal_guide':   'https://edusanjal.com/blog/preparing-for-plus-two-entrance-exams-guide-and-tips/',
    # Brighter Nepal official channels
    'bn_youtube':        'https://www.youtube.com/@BRIGHTERNEPAL1',
    'bn_facebook':       'https://www.facebook.com/p/Brighter-Nepal-61550926048948/',
}


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Tables created.")

        now = datetime.utcnow()

        # ── Groups ────────────────────────────────────────────────────────────
        groups = [
            Group(
                name='Brighter Nepal — +2 Science Bridge Course (Batch 2081)',
                description='Intensive +2 Science Bridge Course for SEE-appeared students. Covers Physics, Chemistry, Mathematics, Biology (Botany & Zoology), Ecology & English. Prepares for St. Xavier\'s, Budhanilkantha, SOS, CCRC, Sainik, KMC & NIST entrance exams.',
                member_count=620,
            ),
            Group(
                name='Brighter Nepal — +2 Management Bridge Course (Batch 2081)',
                description='Advanced Management Bridge Course preparing students for top management colleges. Covers Accountancy, Business Mathematics, Economics, English & GK for Uniglobe, Sifal, Thames, GEMS & other reputed college entrances.',
                member_count=340,
            ),
            Group(
                name='Brighter Nepal — A-Level Science Bridge Course (Batch 2081)',
                description='A-Level (Cambridge AS/A2) Science Bridge Course. Focused on Physics, Chemistry, Mathematics, Biology & General Paper for Lincoln, Rato Bangala, KISC, St. Mary\'s & Summit School admissions.',
                member_count=185,
            ),
            Group(
                name='Brighter Nepal — +2 Humanities Bridge Course (Batch 2081)',
                description='Bridge Course for Humanities stream — Social Studies, Nepali, English, Creative Writing, Optional Mathematics & GK for SEE-appeared students targeting Arts & Social Science colleges.',
                member_count=210,
            ),
            Group(
                name='Brighter Nepal — CTEVT & Diploma Bridge Course (Batch 2081)',
                description='Entrance preparation for CTEVT Diploma programs: Civil, Electrical, Electronics, Computer, Agriculture & Nursing. Covers Science basics, Mathematics, English & GK.',
                member_count=175,
            ),
            Group(
                name='Brighter Nepal — +2 Scholarship Test Batch 2081',
                description='Elite scholarship batch for top-scoring SEE graduates. Intensive preparation for national scholarship tests and reserved seats at premier colleges.',
                member_count=90,
            ),
        ]
        db.session.add_all(groups)
        db.session.flush()

        # ── Admin / Staff ─────────────────────────────────────────────────────
        admin = User(name='Brighter Nepal Admin', email='admin@brighternepal.edu.np',
                     plan='paid', status='active', role='admin', group_id=groups[0].id)
        admin.set_password('BrighterAdmin@2081')
        admin.on_login()
        db.session.add(admin)

        coordinator = User(name='Roshan Paudel', email='coordinator@brighternepal.edu.np',
                           plan='paid', status='active', role='admin', group_id=groups[0].id)
        coordinator.set_password('BrighterAdmin@2081')
        coordinator.on_login()
        db.session.add(coordinator)

        faculty_data = [
            ('Er. Bikash Pokharel',   'bikash.pokharel@brighternepal.edu.np',   groups[0].id),  # Mathematics
            ('Er. Sanjaya Shrestha',  'sanjaya.shrestha@brighternepal.edu.np',  groups[0].id),  # Physics
            ('Mr. Dipendra Karki',    'dipendra.karki@brighternepal.edu.np',    groups[0].id),  # Chemistry
            ('Dr. Kabita Adhikari',   'kabita.adhikari@brighternepal.edu.np',   groups[0].id),  # Biology
            ('Ms. Sunita Thapa',      'sunita.thapa@brighternepal.edu.np',      groups[0].id),  # English
            ('Mr. Pawan Shrestha',    'pawan.shrestha@brighternepal.edu.np',    groups[1].id),  # Accountancy
            ('Ms. Rupa Karmacharya',  'rupa.karmacharya@brighternepal.edu.np',  groups[1].id),  # Economics
            ('Mr. Santosh Gautam',    'santosh.gautam@brighternepal.edu.np',    groups[2].id),  # A-Level Physics
            ('Ms. Priti Basnet',      'priti.basnet@brighternepal.edu.np',      groups[2].id),  # A-Level Chemistry
            ('Mr. Kiran Timalsina',   'kiran.timalsina@brighternepal.edu.np',   groups[3].id),  # Social Studies/GK
            ('Mr. Naresh Bista',      'naresh.bista@brighternepal.edu.np',      groups[4].id),  # CTEVT Science
        ]
        faculty_objs = []
        for fname, femail, fgid in faculty_data:
            fu = User(name=fname, email=femail, plan='paid', status='active', role='admin', group_id=fgid)
            fu.set_password('BrighterAdmin@2081')
            fu.on_login()
            db.session.add(fu)
            faculty_objs.append(fu)

        # ── Students ──────────────────────────────────────────────────────────
        students_data = [
            # +2 Science Bridge
            ('Aashish Maharjan',    'aashish.maharjan@gmail.com',    'paid',  groups[0].id),
            ('Barsha Pandit',       'barsha.pandit@gmail.com',       'paid',  groups[0].id),
            ('Bishal Thapa Magar',  'bishal.thapamagar@gmail.com',   'trial', groups[0].id),
            ('Dibya Shrestha',      'dibya.shrestha@gmail.com',      'paid',  groups[0].id),
            ('Gagan Bista',         'gagan.bista@gmail.com',         'paid',  groups[0].id),
            ('Hema Rana',           'hema.rana@gmail.com',           'trial', groups[0].id),
            ('Ishan Baral',         'ishan.baral@gmail.com',         'paid',  groups[0].id),
            ('Jyoti Khanal',        'jyoti.khanal@gmail.com',        'paid',  groups[0].id),
            ('Kamal Dhungana',      'kamal.dhungana@gmail.com',      'paid',  groups[0].id),
            ('Laxmi Paudel',        'laxmi.paudel@gmail.com',        'trial', groups[0].id),
            ('Milan Chaudhary',     'milan.chaudhary@gmail.com',     'paid',  groups[0].id),
            ('Nisha Lamichhane',    'nisha.lamichhane@gmail.com',    'paid',  groups[0].id),
            ('Om Prakash Dhakal',   'omprakash.dhakal@gmail.com',    'trial', groups[0].id),
            ('Prajwal Acharya',     'prajwal.acharya@gmail.com',     'paid',  groups[0].id),
            ('Rakshya Gurung',      'rakshya.gurung@gmail.com',      'paid',  groups[0].id),
            ('Sagun Neupane',       'sagun.neupane@gmail.com',       'paid',  groups[0].id),
            ('Trishna KC',          'trishna.kc@gmail.com',          'trial', groups[0].id),
            ('Umesh Sapkota',       'umesh.sapkota@gmail.com',       'paid',  groups[0].id),
            # +2 Management
            ('Vibha Joshi',         'vibha.joshi@gmail.com',         'paid',  groups[1].id),
            ('Asmita Rawat',        'asmita.rawat@gmail.com',        'paid',  groups[1].id),
            ('Bikram Tharu',        'bikram.tharu@gmail.com',        'trial', groups[1].id),
            ('Chandrika Adhikari',  'chandrika.adhikari@gmail.com',  'paid',  groups[1].id),
            ('Deepa Lama',          'deepa.lama@gmail.com',          'trial', groups[1].id),
            ('Esha Rijal',          'esha.rijal@gmail.com',          'paid',  groups[1].id),
            ('Farmila Miya',        'farmila.miya@gmail.com',        'paid',  groups[1].id),
            ('Ganesh Koirala',      'ganesh.koirala@gmail.com',      'trial', groups[1].id),
            # A-Level Science
            ('Hamina Gurung',       'hamina.gurung@gmail.com',       'paid',  groups[2].id),
            ('Indreni Bhattarai',   'indreni.bhattarai@gmail.com',   'paid',  groups[2].id),
            ('Jagadish Tamang',     'jagadish.tamang@gmail.com',     'trial', groups[2].id),
            ('Kamana Rai',          'kamana.rai@gmail.com',          'paid',  groups[2].id),
            ('Lila Subedi',         'lila.subedi@gmail.com',         'paid',  groups[2].id),
            # +2 Humanities
            ('Manisha Karki',       'manisha.karki@gmail.com',       'paid',  groups[3].id),
            ('Nabin Ghimire',       'nabin.ghimire@gmail.com',       'trial', groups[3].id),
            ('Ojashwi Shrestha',    'ojashwi.shrestha@gmail.com',    'paid',  groups[3].id),
            ('Pratiksha Poudel',    'pratiksha.poudel@gmail.com',    'paid',  groups[3].id),
            # CTEVT
            ('Rajesh Chaudhary',    'rajesh.chaudhary@gmail.com',    'paid',  groups[4].id),
            ('Sangeeta Limbu',      'sangeeta.limbu@gmail.com',      'trial', groups[4].id),
            ('Tejal Shah',          'tejal.shah@gmail.com',          'paid',  groups[4].id),
            ('Usha Dhakal',         'usha.dhakal@gmail.com',         'paid',  groups[4].id),
            # Scholarship Batch
            ('Vivek Malla',         'vivek.malla@gmail.com',         'paid',  groups[5].id),
            ('Writtika Kafle',      'writtika.kafle@gmail.com',      'paid',  groups[5].id),
            ('Xeniya Pandey',       'xeniya.pandey@gmail.com',       'paid',  groups[5].id),
            ('Yojan Shrestha',      'yojan.shrestha@gmail.com',      'trial', groups[5].id),
            ('Zara Ansari',         'zara.ansari@gmail.com',         'paid',  groups[5].id),
        ]
        student_objs = []
        for name, email, plan, gid in students_data:
            u = User(name=name, email=email, plan=plan, status='active', role='student', group_id=gid)
            u.set_password('Student@2081')
            u.on_login()
            db.session.add(u)
            student_objs.append(u)
        db.session.flush()

        # ── Model Sets ────────────────────────────────────────────────────────
        model_sets = [
            # +2 Science — Top College Entrance Mocks
            ModelSet(title="St. Xavier's College Entrance Mock — Set A (Brighter Nepal 2081)",       difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["StXaviers","+2 Science"]'),
            ModelSet(title="St. Xavier's College Entrance Mock — Set B (Brighter Nepal 2081)",       difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["StXaviers","+2 Science"]'),
            ModelSet(title="St. Xavier's College Entrance Mock — Set C (Brighter Nepal 2081)",       difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["StXaviers","+2 Science"]'),
            ModelSet(title='Budhanilkantha School Entrance Mock — Set A (Brighter Nepal 2081)',      difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["Budhanilkantha","+2 Science"]'),
            ModelSet(title='Budhanilkantha School Entrance Mock — Set B (Brighter Nepal 2081)',      difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["Budhanilkantha","+2 Science"]'),
            ModelSet(title='SOS Hermann Gmeiner +2 Entrance Mock 2081 — Brighter Nepal',            difficulty='Medium', duration_min=90,  total_questions=100, status='published', targets='["SOS","+2 Science"]'),
            ModelSet(title='Sainik Awasiya Vidyamandir Entrance Mock 2081 — Brighter Nepal',        difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["Sainik","+2 Science"]'),
            ModelSet(title='CCRC +2 Science Entrance Mock 2081 — Brighter Nepal',                   difficulty='Medium', duration_min=90,  total_questions=100, status='published', targets='["CCRC","+2 Science"]'),
            ModelSet(title='KMC / NIST / Prasadi Combined Entrance Mock 2081 — Brighter Nepal',     difficulty='Medium', duration_min=90,  total_questions=100, status='published', targets='["KMC","NIST","Prasadi","+2"]'),
            ModelSet(title='Kathmandu Model Secondary School Entrance Mock 2081',                    difficulty='Medium', duration_min=75,  total_questions=75,  status='published', targets='["KMSS","+2 Science"]'),
            ModelSet(title='+2 Science Grand Combined Mock — All Top Colleges 2081',                difficulty='Hard',   duration_min=120, total_questions=100, status='published', targets='["+2 Science","Grand Combined"]'),
            ModelSet(title='+2 Science Physics-Focus Practice Set — Brighter Nepal',               difficulty='Medium', duration_min=60,  total_questions=60,  status='published', targets='["+2 Science","Physics"]'),
            ModelSet(title='+2 Science Biology-Focus Practice Set — Brighter Nepal',               difficulty='Medium', duration_min=60,  total_questions=60,  status='published', targets='["+2 Science","Biology"]'),
            ModelSet(title='+2 Science Chemistry-Focus Practice Set — Brighter Nepal',             difficulty='Medium', duration_min=60,  total_questions=60,  status='published', targets='["+2 Science","Chemistry"]'),
            ModelSet(title='+2 Science Mathematics-Focus Practice Set — Brighter Nepal',           difficulty='Hard',   duration_min=60,  total_questions=60,  status='published', targets='["+2 Science","Mathematics"]'),
            # +2 Management
            ModelSet(title='Uniglobe College Management Entrance Mock 2081 — Brighter Nepal',       difficulty='Medium', duration_min=75,  total_questions=75,  status='published', targets='["+2 Management","Uniglobe"]'),
            ModelSet(title='Sifal School of Finance Entrance Mock 2081 — Brighter Nepal',           difficulty='Medium', duration_min=75,  total_questions=75,  status='published', targets='["+2 Management","Sifal"]'),
            ModelSet(title='Thames International College Entrance Mock 2081 — Brighter Nepal',      difficulty='Medium', duration_min=75,  total_questions=75,  status='published', targets='["+2 Management","Thames"]'),
            ModelSet(title='+2 Management Grand Combined Mock 2081 — Brighter Nepal',              difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["+2 Management","All Colleges"]'),
            # A-Level
            ModelSet(title='A-Level Science Entrance — Lincoln School Mock 2081',                   difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["A-Level","Lincoln"]'),
            ModelSet(title='A-Level Science Entrance — Rato Bangala School Mock 2081',              difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["A-Level","Rato Bangala"]'),
            ModelSet(title="A-Level Combined Mock — KISC & St. Mary's 2081",                        difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["A-Level","KISC","StMarys"]'),
            # CTEVT
            ModelSet(title='CTEVT Diploma Civil Engineering Entrance Mock 2081',                     difficulty='Medium', duration_min=90,  total_questions=75,  status='published', targets='["CTEVT","Civil Diploma"]'),
            ModelSet(title='CTEVT Computer / Electrical Diploma Entrance Mock 2081',                 difficulty='Medium', duration_min=90,  total_questions=75,  status='published', targets='["CTEVT","Computer Diploma","Electrical"]'),
            # Scholarship
            ModelSet(title='National Scholarship +2 Science Practice Set A — Brighter Nepal',       difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["+2 Science","Scholarship"]'),
            ModelSet(title='National Scholarship +2 Science Practice Set B — Brighter Nepal',       difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["+2 Science","Scholarship"]'),
            # Drafts
            ModelSet(title='+2 Science Grand Final Mock — 48-hr Before Entrance 2081',              difficulty='Hard',   duration_min=120, total_questions=100, status='draft',     targets='["+2 Science","Final Prep"]'),
            ModelSet(title='+2 Management Grand Final Mock — 48-hr Before Entrance 2081',           difficulty='Hard',   duration_min=90,  total_questions=100, status='draft',     targets='["+2 Management","Final Prep"]'),
        ]
        db.session.add_all(model_sets)

        # ── Weekly Tests ──────────────────────────────────────────────────────
        tests = [
            WeeklyTest(title='Brighter Nepal Weekly Test — Integration (Definite & Indefinite)',       subject='Mathematics', duration_min=60, status='live',      scheduled_at=now),
            WeeklyTest(title='Brighter Nepal Weekly Test — Light: Reflection & Refraction',            subject='Physics',     duration_min=45, status='scheduled', scheduled_at=now + timedelta(days=1)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Organic Chemistry: Hydrocarbons',           subject='Chemistry',   duration_min=60, status='scheduled', scheduled_at=now + timedelta(days=3)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Cell Biology & Genetics',                   subject='Biology',     duration_min=50, status='scheduled', scheduled_at=now + timedelta(days=5)),
            WeeklyTest(title='Brighter Nepal Weekly Test — English: Grammar & Comprehension',          subject='English',     duration_min=30, status='scheduled', scheduled_at=now + timedelta(days=7)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Coordinate Geometry',                       subject='Mathematics', duration_min=60, status='scheduled', scheduled_at=now + timedelta(days=9)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Electricity & Magnetism',                   subject='Physics',     duration_min=45, status='scheduled', scheduled_at=now + timedelta(days=11)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Ecology & Biodiversity',                    subject='Biology',     duration_min=45, status='scheduled', scheduled_at=now + timedelta(days=13)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Chemical Bonding & Periodicity',            subject='Chemistry',   duration_min=60, status='scheduled', scheduled_at=now + timedelta(days=15)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Accountancy: Journal & Ledger',             subject='Accountancy', duration_min=45, status='scheduled', scheduled_at=now + timedelta(days=16)),
            WeeklyTest(title='Brighter Nepal Weekly Test — General Knowledge & Current Affairs',       subject='GK',          duration_min=30, status='scheduled', scheduled_at=now + timedelta(days=18)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Botany: Plant Kingdom & Physiology',       subject='Biology',     duration_min=50, status='scheduled', scheduled_at=now + timedelta(days=20)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Trigonometry',                              subject='Mathematics', duration_min=60, status='completed', scheduled_at=now - timedelta(days=3)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Mechanics: Motion & Forces',               subject='Physics',     duration_min=45, status='completed', scheduled_at=now - timedelta(days=7)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Atomic Structure & Periodicity',            subject='Chemistry',   duration_min=60, status='completed', scheduled_at=now - timedelta(days=10)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Human Digestive & Circulatory System',     subject='Biology',     duration_min=50, status='completed', scheduled_at=now - timedelta(days=14)),
            WeeklyTest(title='Brighter Nepal Weekly Test — English: Vocabulary & Error Detection',     subject='English',     duration_min=30, status='completed', scheduled_at=now - timedelta(days=17)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Permutations & Probability',               subject='Mathematics', duration_min=60, status='completed', scheduled_at=now - timedelta(days=21)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Heat & Thermodynamics',                    subject='Physics',     duration_min=45, status='completed', scheduled_at=now - timedelta(days=24)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Zoology: Animal Kingdom',                  subject='Biology',     duration_min=50, status='completed', scheduled_at=now - timedelta(days=28)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Electrochemistry',                          subject='Chemistry',   duration_min=60, status='completed', scheduled_at=now - timedelta(days=31)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Sets, Functions & Matrices',               subject='Mathematics', duration_min=45, status='completed', scheduled_at=now - timedelta(days=35)),
        ]
        db.session.add_all(tests)
        db.session.flush()

        # ── Question Bank ─────────────────────────────────────────────────────
        def add_qs(subject, q_list):
            objs = []
            for text, options, ans_idx in q_list:
                q = Question(subject=subject, text=text,
                             options=json.dumps(options), answer_index=ans_idx)
                db.session.add(q)
                objs.append(q)
            db.session.flush()
            return objs

        # MATHEMATICS — 25 Qs
        math_qs = add_qs('Mathematics', [
            ('Evaluate ∫(3x² + 2x − 5) dx',                                       ['x³ + x² − 5x + C', 'x³ + x² + 5x + C', '6x + 2 + C', '3x³ + 2x² + C'], 0),
            ('What is ∫sin(x) dx?',                                                ['−cos(x) + C', 'cos(x) + C', 'sec(x) + C', 'tan(x) + C'], 0),
            ('Evaluate ∫₀² x³ dx.',                                                ['4', '8', '2', '16'], 0),
            ('Integration method for ∫x·eˣ dx is:',                               ['Integration by Parts', 'Substitution', 'Partial Fractions', 'Direct Integration'], 0),
            ('Find ∫(1/x) dx for x > 0.',                                          ['ln|x| + C', '1/x² + C', 'x + C', '−1/x + C'], 0),
            ('Evaluate ∫cos²(x) dx.',                                              ['x/2 + sin(2x)/4 + C', 'sin²(x) + C', 'x + C', 'cos(x)sin(x) + C'], 0),
            ('Area under y = x² from x=0 to x=3 is:',                             ['9', '27', '3', '6'], 0),
            ('If F(x) = ∫₁ˣ t² dt, then F\'(x) = ?',                              ['x²', '2x', '1', 'x³/3'], 0),
            ('Evaluate ∫(2x+3)⁵ dx.',                                              ['(2x+3)⁶/12 + C', '(2x+3)⁶/6 + C', '5(2x+3)⁴ + C', '(2x+3)⁶ + C'], 0),
            ('Derivative of tan(x) is:',                                           ['sec²(x)', 'cot²(x)', '−csc²(x)', 'sin²(x)'], 0),
            ('f(x) = x³ − 3x + 2. Find f\'(1).',                                  ['0', '3', '−3', '2'], 0),
            ('Period of sin(2x) is:',                                              ['π', '2π', 'π/2', '4π'], 0),
            ('sin(45°) × cos(45°) = ?',                                            ['1/2', '√2/2', '1', '√2'], 0),
            ('If log₂(8) = x, then x = ?',                                        ['3', '2', '4', '8'], 0),
            ('Number of diagonals in a hexagon:',                                  ['9', '6', '12', '15'], 0),
            ('Sum of interior angles of a pentagon:',                              ['540°', '360°', '720°', '480°'], 0),
            ('Slope of line through (2,3) and (4,7):',                            ['2', '1', '4', '1/2'], 0),
            ('Ways to arrange 5 people in a row:',                                 ['120', '60', '24', '720'], 0),
            ('P(A)=0.4, P(B)=0.3, P(A∩B)=0.1. P(A∪B) = ?',                    ['0.6', '0.7', '0.5', '0.4'], 0),
            ('det([[1,2],[3,4]]) = ?',                                             ['−2', '2', '10', '−10'], 0),
            ('Distance between (0,0) and (3,4):',                                  ['5', '7', '4', '3'], 0),
            ('Circle with centre (0,0), radius 5:',                               ['x² + y² = 25', 'x² + y² = 5', 'x + y = 25', '(x+y)² = 25'], 0),
            ('2³ × 2² = ?',                                                        ['32', '16', '8', '64'], 0),
            ('x + y = 10 and x − y = 4. Find x.',                                 ['7', '3', '5', '6'], 0),
            ('cos(0°) = ?',                                                        ['1', '0', '−1', '√2/2'], 0),
        ])

        # PHYSICS — 25 Qs
        physics_qs = add_qs('Physics', [
            ('Faraday\'s law relates EMF to rate of change of:',                   ['Magnetic flux', 'Electric flux', 'Current', 'Voltage'], 0),
            ('SI unit of magnetic flux:',                                           ['Weber (Wb)', 'Tesla (T)', 'Henry (H)', 'Ampere (A)'], 0),
            ('Lenz\'s law is based on conservation of:',                           ['Energy', 'Charge', 'Momentum', 'Mass'], 0),
            ('Transformer: Np/Ns = 10. Ratio Vs/Vp = ?',                          ['0.1', '10', '1', '100'], 0),
            ('SI unit of self-inductance:',                                         ['Henry (H)', 'Farad (F)', 'Ohm (Ω)', 'Tesla (T)'], 0),
            ('Speed of light in vacuum:',                                           ['3×10⁸ m/s', '3×10⁶ m/s', '3×10¹⁰ m/s', '3×10⁴ m/s'], 0),
            ('Newton\'s Second Law: F = ?',                                        ['ma', 'm/a', 'mv', 'm/v'], 0),
            ('"For every action there is equal and opposite reaction" is:',        ['Newton\'s 3rd Law', '1st Law', '2nd Law', 'Law of Gravity'], 0),
            ('SI unit of pressure:',                                               ['Pascal (Pa)', 'Newton (N)', 'Joule (J)', 'Watt (W)'], 0),
            ('Rainbow is caused by:',                                              ['Dispersion of light', 'Reflection', 'Diffraction', 'Polarization'], 0),
            ('Work done is zero when force and displacement are:',                 ['Perpendicular', 'Parallel', 'Anti-parallel', 'Equal'], 0),
            ('Critical angle for TIR depends on:',                                 ['Refractive index', 'Wavelength', 'Frequency', 'Amplitude'], 0),
            ('Ohm\'s Law: V = ?',                                                  ['IR', 'I/R', 'I + R', 'I²R'], 0),
            ('Which particle has no charge?',                                      ['Neutron', 'Proton', 'Electron', 'Positron'], 0),
            ('Boyle\'s Law at constant temperature: P ∝ ?',                       ['1/V', 'V', 'T', '1/T'], 0),
            ('Energy stored in a spring:',                                         ['½kx²', 'kx²', '2kx', 'kx'], 0),
            ('Relation between frequency f and time period T:',                    ['f = 1/T', 'f = T', 'f = T²', 'f = 2T'], 0),
            ('Acceleration due to gravity on Earth\'s surface ≈',                 ['9.8 m/s²', '9.8 km/s²', '8.9 m/s²', '10.8 m/s²'], 0),
            ('Rear-view mirror in vehicles is:',                                   ['Convex', 'Concave', 'Plane', 'Parabolic'], 0),
            ('Angle of incidence = Angle of reflection is:',                       ['Law of Reflection', 'Snell\'s Law', 'Law of Refraction', 'Brewster\'s Law'], 0),
            ('Body in uniform circular motion has:',                               ['Centripetal acceleration', 'Zero acceleration', 'Only tangential acceleration', 'No force'], 0),
            ('Bernoulli\'s principle conserves:',                                  ['Energy', 'Momentum', 'Mass', 'Charge'], 0),
            ('SI unit of electric charge:',                                        ['Coulomb (C)', 'Ampere (A)', 'Volt (V)', 'Ohm (Ω)'], 0),
            ('Kinetic energy = ?',                                                 ['½mv²', 'mv²', 'mgh', '½mv'], 0),
            ('Photons are quanta of:',                                             ['Electromagnetic radiation', 'Sound', 'Matter', 'Heat'], 0),
        ])

        # CHEMISTRY — 25 Qs
        chemistry_qs = add_qs('Chemistry', [
            ('General formula of alkanes:',                                        ['CₙH₂ₙ₊₂', 'CₙH₂ₙ', 'CₙH₂ₙ₋₂', 'CₙHₙ'], 0),
            ('IUPAC name of CH₃−CH₂−CH₂−CH₃:',                                  ['Butane', 'Propane', 'Pentane', 'Methane'], 0),
            ('Reaction converting alkene → alkane:',                               ['Hydrogenation', 'Halogenation', 'Combustion', 'Dehydration'], 0),
            ('Benzene primarily undergoes:',                                        ['Electrophilic substitution', 'Nucleophilic addition', 'Free-radical addition', 'Elimination'], 0),
            ('Markovnikov\'s rule applies to:',                                    ['Alkenes', 'Alkanes', 'Alkynes only', 'Benzene'], 0),
            ('Atomic number of Carbon:',                                           ['6', '8', '12', '4'], 0),
            ('pH of pure water at 25°C:',                                          ['7', '0', '14', '10'], 0),
            ('Gas produced when Zn reacts with dil. H₂SO₄:',                     ['H₂', 'O₂', 'CO₂', 'SO₂'], 0),
            ('Chemical formula of table salt:',                                    ['NaCl', 'Na₂SO₄', 'NaOH', 'NaNO₃'], 0),
            ('Avogadro\'s number:',                                                ['6.022×10²³', '6.022×10²²', '1.602×10⁻¹⁹', '9.109×10⁻³¹'], 0),
            ('Highest electronegativity element:',                                 ['Fluorine (F)', 'Oxygen (O)', 'Chlorine (Cl)', 'Nitrogen (N)'], 0),
            ('Gaining of electrons is called:',                                    ['Reduction', 'Oxidation', 'Hydrolysis', 'Electrolysis'], 0),
            ('Bond type in H₂O:',                                                  ['Covalent bond', 'Ionic bond', 'Metallic bond', 'Hydrogen bond only'], 0),
            ('Catalyst in Haber process (NH₃ synthesis):',                        ['Iron (Fe)', 'Platinum (Pt)', 'Vanadium pentoxide (V₂O₅)', 'Nickel (Ni)'], 0),
            ('Molar mass of CO₂:',                                                 ['44 g/mol', '28 g/mol', '32 g/mol', '40 g/mol'], 0),
            ('Le Chatelier\'s principle deals with:',                              ['Equilibrium systems', 'Reaction rate only', 'Bond energy', 'pH only'], 0),
            ('N₂ molecule has:',                                                   ['Triple bond', 'Single bond', 'Double bond', 'No bond'], 0),
            ('Empirical formula of glucose (C₆H₁₂O₆):',                          ['CH₂O', 'C₂H₄O₂', 'C₃H₆O₃', 'C₆H₁₂O₆'], 0),
            ('An acid has pH:',                                                    ['Less than 7', 'More than 7', 'Equal to 7', 'Equal to 14'], 0),
            ('Electrolysis of NaCl solution gives:',                              ['Cl₂ at anode, H₂ at cathode', 'O₂ at anode, Na at cathode', 'H₂ at anode, Cl₂ at cathode', 'Na and Cl₂ at cathode'], 0),
            ('IUPAC name of CH₃COOH:',                                            ['Ethanoic acid', 'Methanolic acid', 'Propanoic acid', 'Butanoic acid'], 0),
            ('Isomers have:',                                                      ['Same molecular formula, different structure', 'Same structural formula', 'Same physical properties', 'Same melting point'], 0),
            ('Acid in a car battery:',                                             ['H₂SO₄ (sulphuric acid)', 'HCl (hydrochloric)', 'HNO₃ (nitric acid)', 'H₃PO₄ (phosphoric acid)'], 0),
            ('Glucose → alcohol is:',                                              ['Fermentation', 'Combustion', 'Hydrogenation', 'Oxidation'], 0),
            ('Metals in the periodic table are found on the:',                    ['Left side', 'Right side', 'Middle only', 'Top row only'], 0),
        ])

        # BIOLOGY — Zoology (20 Qs)
        zoology_qs = add_qs('Biology', [
            ('DNA replication is:',                                                ['Semi-conservative', 'Conservative', 'Dispersive', 'Asymmetric'], 0),
            ('"Powerhouse of the cell":',                                          ['Mitochondria', 'Ribosome', 'Golgi apparatus', 'Lysosome'], 0),
            ('Meiosis produces:',                                                  ['4 haploid cells', '2 diploid cells', '4 diploid cells', '2 haploid cells'], 0),
            ('Mendel\'s law of segregation states alleles:',                      ['Separate during gamete formation', 'Blend together', 'Are always dominant', 'Are linked always'], 0),
            ('Thymine pairs with:',                                                ['Adenine', 'Guanine', 'Cytosine', 'Uracil'], 0),
            ('Cellular respiration produces:',                                     ['ATP (energy)', 'Glucose', 'CO₂ only', 'H₂O only'], 0),
            ('Human heart chambers:',                                              ['4', '2', '3', '6'], 0),
            ('Blood pumped to body via:',                                          ['Aorta', 'Vena cava', 'Pulmonary artery', 'Coronary artery'], 0),
            ('Universal donor blood group:',                                       ['O negative', 'AB positive', 'A positive', 'B negative'], 0),
            ('Largest organ in the human body:',                                   ['Skin', 'Liver', 'Brain', 'Lung'], 0),
            ('Insulin is produced by:',                                            ['Pancreas', 'Liver', 'Kidney', 'Adrenal gland'], 0),
            ('Functional unit of kidney:',                                         ['Nephron', 'Neuron', 'Alveolus', 'Villus'], 0),
            ('Muscle type in the heart:',                                          ['Cardiac muscle', 'Smooth muscle', 'Skeletal muscle', 'Striated (voluntary)'], 0),
            ('Largest bone in the human body:',                                    ['Femur', 'Tibia', 'Humerus', 'Fibula'], 0),
            ('Chromosome pairs in human somatic cell:',                            ['23 pairs (46 total)', '24 pairs', '22 pairs', '46 pairs (92 total)'], 0),
            ('Study of heredity and variation:',                                   ['Genetics', 'Ecology', 'Evolution', 'Taxonomy'], 0),
            ('Haemoglobin primarily carries:',                                     ['Oxygen', 'Carbon dioxide', 'Glucose', 'Nutrients'], 0),
            ('Fertilization in humans occurs in:',                                 ['Fallopian tube', 'Uterus', 'Ovary', 'Vagina'], 0),
            ('Reflex actions are controlled by:',                                  ['Spinal cord', 'Cerebrum', 'Cerebellum', 'Medulla'], 0),
            ('Sunlight helps produce which vitamin in skin?',                      ['Vitamin D', 'Vitamin A', 'Vitamin C', 'Vitamin K'], 0),
        ])

        # BIOLOGY — Botany (15 Qs)
        botany_qs = add_qs('Biology', [
            ('Plants make food using sunlight through:',                           ['Photosynthesis', 'Respiration', 'Transpiration', 'Germination'], 0),
            ('Chlorophyll is found in:',                                           ['Chloroplast', 'Mitochondria', 'Ribosome', 'Nucleus'], 0),
            ('Raw materials for photosynthesis:',                                  ['CO₂ and H₂O', 'O₂ and glucose', 'N₂ and H₂O', 'CO₂ and O₂'], 0),
            ('Water and minerals conducted by:',                                   ['Xylem', 'Phloem', 'Cortex', 'Epidermis'], 0),
            ('Which flower part becomes the fruit?',                               ['Ovary', 'Petal', 'Sepal', 'Stamen'], 0),
            ('Stomata opening/closing controlled by:',                             ['Guard cells', 'Epidermis', 'Mesophyll cells', 'Root hairs'], 0),
            ('Loss of water vapour from leaves:',                                  ['Transpiration', 'Evaporation', 'Guttation', 'Absorption'], 0),
            ('Plant hormone promoting cell elongation:',                           ['Auxin (IAA)', 'Gibberellin', 'Cytokinin', 'Abscisic acid'], 0),
            ('Male reproductive organ of a flower:',                               ['Stamen (anther+filament)', 'Pistil', 'Petal', 'Sepal'], 0),
            ('Roots absorb water through:',                                        ['Osmosis', 'Diffusion', 'Active transport', 'Filtration'], 0),
            ('Green pigment in plants:',                                           ['Chlorophyll', 'Carotenoid', 'Anthocyanin', 'Xanthophyll'], 0),
            ('Ferns reproduce through:',                                           ['Spores', 'Seeds', 'Flowers', 'Bulbs'], 0),
            ('Food-conducting tissue in plants:',                                  ['Phloem', 'Xylem', 'Parenchyma', 'Sclerenchyma'], 0),
            ('Gaseous exchange in plants via:',                                    ['Stomata', 'Root hair', 'Bark', 'Xylem'], 0),
            ('Gymnosperms have:',                                                  ['Naked seeds', 'Enclosed seeds', 'No seeds', 'Spores only'], 0),
        ])

        # BIOLOGY — Ecology (10 Qs)
        ecology_qs = add_qs('Biology', [
            ('Role of an organism in an ecosystem:',                               ['Niche', 'Habitat', 'Biome', 'Territory'], 0),
            ('Producers in an ecosystem are:',                                     ['Green plants', 'Herbivores', 'Carnivores', 'Decomposers'], 0),
            ('Primary greenhouse gas:',                                            ['CO₂', 'O₂', 'N₂', 'H₂'], 0),
            ('IUCN stands for:',                                                   ['International Union for Conservation of Nature', 'International Union for Climate Needs', 'Integrated Union for Conservation Networks', 'International Unit for Conservation Norms'], 0),
            ('In: Grass→Grasshopper→Frog→Snake, Grass is:',                      ['Producer', 'Primary consumer', 'Secondary consumer', 'Decomposer'], 0),
            ('Classification of organisms is called:',                             ['Taxonomy', 'Ecology', 'Morphology', 'Physiology'], 0),
            ('Ozone layer is in which atmosphere layer?',                          ['Stratosphere', 'Troposphere', 'Mesosphere', 'Thermosphere'], 0),
            ('Term "biodiversity" coined by:',                                     ['E.O. Wilson', 'Charles Darwin', 'Gregor Mendel', 'Carl Linnaeus'], 0),
            ('Decomposers break down:',                                            ['Dead organic matter', 'Living plants', 'Sunlight', 'Mineral rocks'], 0),
            ('National parks are examples of:',                                    ['In-situ conservation', 'Ex-situ conservation', 'Both', 'Neither'], 0),
        ])

        # ENGLISH — 20 Qs
        english_qs = add_qs('English', [
            ('"___ honest man is trustworthy." Correct article:',                  ['An', 'A', 'The', 'No article'], 0),
            ('Error in: "She don\'t like coffee."',                               ['don\'t → doesn\'t', 'She → Her', 'like → likes', 'No error'], 0),
            ('Synonym of "benevolent":',                                           ['Kind', 'Cruel', 'Selfish', 'Rude'], 0),
            ('Antonym of "verbose":',                                              ['Concise', 'Talkative', 'Wordy', 'Loquacious'], 0),
            ('Passive of "She wrote a letter":',                                   ['A letter was written by her', 'A letter is written by her', 'A letter had been written', 'A letter will be written by her'], 0),
            ('Correct sentence (subject-verb agreement):',                         ['"Neither the students nor the teacher was present."', '"Neither the students nor the teacher were present."', '"Neither the students nor the teacher are present."', '"Neither the students nor the teacher have been present."'], 0),
            ('"Ameliorate" means:',                                                ['To improve', 'To worsen', 'To destroy', 'To delay'], 0),
            ('"The pen is mightier than the sword." Figure of speech:',           ['Metaphor', 'Simile', 'Alliteration', 'Hyperbole'], 0),
            ('"I look forward ___ meeting you."',                                  ['to', 'for', 'at', 'with'], 0),
            ('"She has been living here ___ 2010."',                              ['since', 'for', 'from', 'until'], 0),
            ('Which is a compound sentence?',                                      ['"I went to school, and she stayed home."', '"Because it rained, the match was cancelled."', '"He runs fast."', '"The tall boy won."'], 0),
            ('Plural of "phenomenon":',                                            ['Phenomena', 'Phenomenons', 'Phenomenon', 'Phenomenas'], 0),
            ('"Burning the midnight oil" means:',                                  ['Working late at night', 'Wasting energy', 'Setting fire to oil', 'Sleeping all day'], 0),
            ('She said, "I am tired." Indirect speech:',                           ['She said that she was tired.', 'She said that I am tired.', 'She said that she is tired.', 'She told I was tired.'], 0),
            ('Past participle of "go":',                                           ['Gone', 'Went', 'Goes', 'Going'], 0),
            ('"Neither of the boys ___ present."',                                 ['was', 'were', 'are', 'have been'], 0),
            ('"The stars danced in the sky." Figure of speech:',                   ['Personification', 'Simile', 'Metaphor', 'Hyperbole'], 0),
            ('"Omniscient" means:',                                                ['All-knowing', 'All-powerful', 'All-present', 'All-forgiving'], 0),
            ('"Carte blanche" means:',                                             ['Unlimited authority', 'White card', 'Blank cheque literally', 'French cuisine'], 0),
            ('"The committee ___ divided on the issue."',                          ['was', 'were', 'is', 'are'], 0),
        ])

        # GENERAL KNOWLEDGE — 15 Qs
        gk_qs = add_qs('GK', [
            ('Founding father (unifier) of Nepal:',                               ['Prithvi Narayan Shah', 'King Mahendra', 'Birendra Shah', 'Tribhuvan Shah'], 0),
            ('Highest mountain in the world:',                                     ['Mount Everest', 'K2', 'Kangchenjunga', 'Lhotse'], 0),
            ('Nepal became a Federal Democratic Republic in:',                     ['2008 (2065 BS)', '2006 (2063 BS)', '1990 (2047 BS)', '2015 (2072 BS)'], 0),
            ('Currency of Nepal:',                                                 ['Nepalese Rupee (NPR)', 'Indian Rupee (INR)', 'Nepali Taka', 'Nepalese Dollar'], 0),
            ('Largest lake in Nepal:',                                             ['Rara Lake', 'Phewa Lake', 'Tilicho Lake', 'Gosaikunda Lake'], 0),
            ('Nepal has how many provinces?',                                      ['7', '5', '3', '9'], 0),
            ('SEE stands for:',                                                    ['Secondary Education Examination', 'Secondary Elementary Exam', 'Science Education Entrance', 'Secondary English Evaluation'], 0),
            ('National flower of Nepal:',                                          ['Lali Gurans (Rhododendron)', 'Lotus', 'Rose', 'Marigold'], 0),
            ('Nepal national anthem written by:',                                  ['Byakul Maila', 'Lekhnath Paudyal', 'Mahakavi Devkota', 'Bhanubhakta Acharya'], 0),
            ('NEB stands for:',                                                    ['National Examinations Board', 'Nepal Education Bureau', 'National Education Body', 'Nepal Examination Branch'], 0),
            ('WHO stands for:',                                                    ['World Health Organization', 'World Heritage Organization', 'World Humanitarian Organization', 'World Health Office'], 0),
            ('Capital of Nepal:',                                                  ['Kathmandu', 'Pokhara', 'Lalitpur', 'Biratnagar'], 0),
            ('Which is a UN Sustainable Development Goal?',                        ['No Poverty', 'Universal Currency', 'Unlimited Energy', 'No Government'], 0),
            ("St. Xavier's College (Nepal) is located at:",                        ['Maitighar, Kathmandu', 'Lazimpat, Kathmandu', 'Thamel, Kathmandu', 'Patan, Lalitpur'], 0),
            ('Budhanilkantha School is in:',                                       ['Budhanilkantha, Kathmandu', 'Bhaktapur', 'Lalitpur', 'Kavre'], 0),
        ])

        # ACCOUNTANCY — 15 Qs
        acc_qs = add_qs('Accountancy', [
            ('Accounting equation:',                                               ['Assets = Liabilities + Owner\'s Equity', 'Assets = Capital − Liabilities', 'Liabilities = Assets + Capital', 'Capital = Assets × Liabilities'], 0),
            ('Financial statement showing profit or loss:',                        ['Income Statement (P&L)', 'Balance Sheet', 'Cash Flow Statement', 'Trial Balance'], 0),
            ('Double-entry system: every transaction has:',                        ['A debit and a credit entry', 'Two debit entries', 'Two credit entries', 'One ledger entry'], 0),
            ('Depreciation is charged on:',                                        ['Fixed assets', 'Current assets', 'Liabilities', 'Capital'], 0),
            ('Normal debit balance accounts:',                                     ['Assets & Expenses', 'Revenue & Liabilities', 'Capital & Revenue', 'None of these'], 0),
            ('Trade discount is:',                                                 ['Deducted from invoice price', 'Added to invoice price', 'Recorded in cash book', 'Given for prompt payment only'], 0),
            ('Current assets include:',                                            ['Cash, debtors, inventory', 'Land, building, machinery', 'Loans, debentures', 'Capital and reserves'], 0),
            ('FIFO stands for:',                                                   ['First In First Out', 'First Invoice First Out', 'Fixed Income Financial Order', 'First In Final Output'], 0),
            ('Goodwill is:',                                                       ['Intangible fixed asset', 'Tangible fixed asset', 'Current asset', 'Fictitious asset'], 0),
            ('VAT stands for:',                                                    ['Value Added Tax', 'Variable Asset Tax', 'Value Allocation Tax', 'Various Asset Tax'], 0),
            ('Working capital = ?',                                                ['Current Assets − Current Liabilities', 'Fixed Assets − Current Liabilities', 'Total Assets − Total Liabilities', 'Capital − Liabilities'], 0),
            ('Bank reconciliation statement reconciles:',                          ['Bank balance with cash book', 'Income vs expenses', 'Bank vs debtors', 'Assets vs liabilities'], 0),
            ('Closing stock appears in:',                                          ['Balance Sheet & Trading Account', 'Income Statement only', 'Cash Flow only', 'Ledger only'], 0),
            ('Provision for bad debts is a:',                                      ['Contra asset account', 'Liability account', 'Revenue account', 'Capital account'], 0),
            ('Costs matched with revenues is the:',                                ['Matching principle', 'Going concern', 'Accrual concept', 'Consistency principle'], 0),
        ])

        all_qs = (math_qs + physics_qs + chemistry_qs + zoology_qs +
                  botany_qs + ecology_qs + english_qs + gk_qs + acc_qs)
        db.session.flush()

        # ── Link Questions → Weekly Tests ─────────────────────────────────────
        test_q_map = [
            (tests[0],  math_qs[:10]),
            (tests[1],  physics_qs[:10]),
            (tests[2],  chemistry_qs[:10]),
            (tests[3],  zoology_qs[:10]),
            (tests[4],  english_qs[:10]),
            (tests[5],  math_qs[10:]),
            (tests[6],  physics_qs[10:]),
            (tests[7],  ecology_qs),
            (tests[8],  chemistry_qs[10:]),
            (tests[9],  acc_qs[:10]),
            (tests[10], gk_qs),
            (tests[11], botany_qs[:10]),
            (tests[12], math_qs[:8]),
            (tests[13], physics_qs[:8]),
            (tests[14], chemistry_qs[:8]),
            (tests[15], zoology_qs[10:]),
            (tests[16], english_qs[10:]),
            (tests[17], math_qs[8:16]),
            (tests[18], physics_qs[8:16]),
            (tests[19], botany_qs),
            (tests[20], chemistry_qs[8:16]),
            (tests[21], math_qs[4:12]),
        ]
        for test, q_list in test_q_map:
            for idx, q in enumerate(q_list):
                db.session.add(WeeklyTestQuestion(test_id=test.id, question_id=q.id, order_index=idx))

        # ── Link Questions → Model Sets ────────────────────────────────────────
        science_pool = (math_qs + physics_qs + chemistry_qs +
                        zoology_qs[:10] + botany_qs[:10] + ecology_qs +
                        english_qs[:10] + gk_qs)
        management_pool = math_qs[:15] + english_qs + acc_qs + gk_qs

        for ms in model_sets[:15]:    # +2 Science sets
            pool = science_pool[:ms.total_questions]
            for idx, q in enumerate(pool):
                db.session.add(ModelSetQuestion(model_set_id=ms.id, question_id=q.id, order_index=idx))
        for ms in model_sets[15:19]:  # Management sets
            pool = management_pool[:ms.total_questions]
            for idx, q in enumerate(pool):
                db.session.add(ModelSetQuestion(model_set_id=ms.id, question_id=q.id, order_index=idx))
        for ms in model_sets[19:22]:  # A-Level sets
            pool = science_pool[:ms.total_questions]
            for idx, q in enumerate(pool):
                db.session.add(ModelSetQuestion(model_set_id=ms.id, question_id=q.id, order_index=idx))

        # ── Live Classes ──────────────────────────────────────────────────────
        classes = [
            # Live
            LiveClass(title='Definite Integration: Techniques & +2 Science Entrance Past Questions',             teacher='Er. Bikash Pokharel (Brighter Nepal)',   subject='Mathematics', duration_min=90,  status='live',      watchers=2800, scheduled_at=now),
            # Upcoming
            LiveClass(title="Reflection & Refraction of Light — St. Xavier's & Budhanilkantha Focus",            teacher='Er. Sanjaya Shrestha (Brighter Nepal)',  subject='Physics',     duration_min=75,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(hours=3)),
            LiveClass(title='Aliphatic Compounds: Alkanes, Alkenes & Alkynes — Bridge Course Chemistry',         teacher='Mr. Dipendra Karki (Brighter Nepal)',    subject='Chemistry',   duration_min=80,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(hours=6)),
            LiveClass(title='Cell Division: Mitosis vs Meiosis — Bridge Course Biology Session',                 teacher='Dr. Kabita Adhikari (Brighter Nepal)',   subject='Biology',     duration_min=60,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(hours=10)),
            LiveClass(title='English Grammar: Subject-Verb Agreement & Error Detection — Bridge Course',         teacher='Ms. Sunita Thapa (Brighter Nepal)',      subject='English',     duration_min=55,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=2)),
            LiveClass(title='Coordinate Geometry: Lines & Circles — +2 Science Entrance Prep',                   teacher='Er. Bikash Pokharel (Brighter Nepal)',   subject='Mathematics', duration_min=90,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=3)),
            LiveClass(title='Electricity & Magnetism — Brighter Nepal Bridge Course Session',                    teacher='Er. Sanjaya Shrestha (Brighter Nepal)',  subject='Physics',     duration_min=75,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=4)),
            LiveClass(title='Aromatic Chemistry & Named Reactions — Bridge Course',                              teacher='Mr. Dipendra Karki (Brighter Nepal)',    subject='Chemistry',   duration_min=80,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=5)),
            LiveClass(title='Botany: Photosynthesis & Plant Kingdom — Bridge Course Deep Dive',                  teacher='Dr. Kabita Adhikari (Brighter Nepal)',   subject='Biology',     duration_min=60,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=6)),
            LiveClass(title='Accountancy Basics: Journal, Ledger & Trial Balance — Management Batch',            teacher='Mr. Pawan Shrestha (Brighter Nepal)',    subject='Accountancy', duration_min=75,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=7)),
            LiveClass(title="Ecology & Biodiversity: Nepal's Flora & Fauna — Bridge Course",                     teacher='Dr. Kabita Adhikari (Brighter Nepal)',   subject='Biology',     duration_min=60,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=9)),
            LiveClass(title='Trigonometry: Identities, Formulae & Practice Problems',                            teacher='Er. Bikash Pokharel (Brighter Nepal)',   subject='Mathematics', duration_min=90,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=10)),
            LiveClass(title='Human Body Systems: Digestive, Circulatory & Nervous — Bridge Course',              teacher='Dr. Kabita Adhikari (Brighter Nepal)',   subject='Biology',     duration_min=65,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=11)),
            LiveClass(title='Economics: Demand, Supply & Market Analysis — Management Batch',                    teacher='Ms. Rupa Karmacharya (Brighter Nepal)',  subject='Economics',   duration_min=70,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=12)),
            LiveClass(title='General Knowledge & Current Affairs — All Batches Open Session',                    teacher='Mr. Kiran Timalsina (Brighter Nepal)',   subject='GK',          duration_min=50,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=14)),
            LiveClass(title='Differential Calculus: Limits, Continuity & Differentiation',                      teacher='Er. Bikash Pokharel (Brighter Nepal)',   subject='Mathematics', duration_min=100, status='completed', watchers=0, scheduled_at=now - timedelta(days=4)),
            LiveClass(title='Optics: Refraction & Total Internal Reflection — Bridge Course',                    teacher='Er. Sanjaya Shrestha (Brighter Nepal)',  subject='Physics',     duration_min=110, status='completed', watchers=0, scheduled_at=now - timedelta(days=7)),
            LiveClass(title='Atomic Structure & Chemical Bonding — Bridge Course Chemistry',                     teacher='Mr. Dipendra Karki (Brighter Nepal)',    subject='Chemistry',   duration_min=90,  status='completed', watchers=0, scheduled_at=now - timedelta(days=10)),
            LiveClass(title="Genetics: Mendel's Laws & Chromosomal Theory — Bridge Course",                      teacher='Dr. Kabita Adhikari (Brighter Nepal)',   subject='Biology',     duration_min=75,  status='completed', watchers=0, scheduled_at=now - timedelta(days=13)),
            LiveClass(title='Trigonometry: Sin, Cos, Tan, Identities & Applications',                           teacher='Er. Bikash Pokharel (Brighter Nepal)',   subject='Mathematics', duration_min=105, status='completed', watchers=0, scheduled_at=now - timedelta(days=16)),
            LiveClass(title="Current Electricity: Ohm's Law & Kirchhoff's Laws",                                teacher='Er. Sanjaya Shrestha (Brighter Nepal)',  subject='Physics',     duration_min=90,  status='completed', watchers=0, scheduled_at=now - timedelta(days=20)),
            LiveClass(title='Gaseous State & Solutions — Bridge Course Physical Chemistry',                      teacher='Mr. Dipendra Karki (Brighter Nepal)',    subject='Chemistry',   duration_min=80,  status='completed', watchers=0, scheduled_at=now - timedelta(days=23)),
            LiveClass(title='Human Reproductive System — +2 Science Bridge Course Biology',                     teacher='Dr. Kabita Adhikari (Brighter Nepal)',   subject='Biology',     duration_min=70,  status='completed', watchers=0, scheduled_at=now - timedelta(days=27)),
            LiveClass(title='Vocabulary & Comprehension — English Bridge Course Session',                        teacher='Ms. Sunita Thapa (Brighter Nepal)',      subject='English',     duration_min=60,  status='completed', watchers=0, scheduled_at=now - timedelta(days=30)),
            LiveClass(title='Nepal GK: History, Geography & Current Affairs — All Batches',                     teacher='Mr. Kiran Timalsina (Brighter Nepal)',   subject='GK',          duration_min=55,  status='completed', watchers=0, scheduled_at=now - timedelta(days=34)),
            LiveClass(title='Financial Accounting: Double Entry, Journal & Ledger — Management',                 teacher='Mr. Pawan Shrestha (Brighter Nepal)',    subject='Accountancy', duration_min=75,  status='completed', watchers=0, scheduled_at=now - timedelta(days=37)),
        ]
        db.session.add_all(classes)
        db.session.flush()   # gives IDs to live classes so we can FK-reference them below

        # Map subject → completed class ID, used to link resources to recordings
        _cls_by_title = {c.title: c.id for c in classes if c.status == 'completed'}
        _math_cls    = _cls_by_title.get('Differential Calculus: Limits, Continuity & Differentiation')
        _trig_cls    = _cls_by_title.get('Trigonometry: Sin, Cos, Tan, Identities & Applications')
        _physics_cls = _cls_by_title.get('Optics: Refraction & Total Internal Reflection — Bridge Course')
        _elec_cls    = _cls_by_title.get("Current Electricity: Ohm's Law & Kirchhoff's Laws")
        _chem_cls    = _cls_by_title.get('Atomic Structure & Chemical Bonding — Bridge Course Chemistry')
        _chem2_cls   = _cls_by_title.get('Gaseous State & Solutions — Bridge Course Physical Chemistry')
        _bio_cls     = _cls_by_title.get("Genetics: Mendel's Laws & Chromosomal Theory — Bridge Course")
        _bio2_cls    = _cls_by_title.get('Human Reproductive System — +2 Science Bridge Course Biology')
        _eng_cls     = _cls_by_title.get('Vocabulary & Comprehension — English Bridge Course Session')

        # ── Resources (real file_url) ─────────────────────────────────────────
        resources = [
            # College Model Questions (real links)
            Resource(title='Top Colleges +2 Entrance Model Questions — StudyNotesNepal',
                     subject='Mathematics', format='pdf', section='College Model Questions',
                     size_label='4.8 MB', downloads=7200,
                     tags='["Entrance","Model Q","StXaviers","Budhanilkantha","Top Colleges"]',
                     file_url=REAL_LINKS['top_college_q']),
            Resource(title="+2 Entrance Practice Set 1 — St. Xavier's Based (StudyNotesNepal)",
                     subject='Mathematics', format='pdf', section='College Model Questions',
                     size_label='3.2 MB', downloads=6800,
                     tags='["Practice","StXaviers","Entrance","MCQ"]',
                     file_url=REAL_LINKS['practice_set1']),
            Resource(title='After SEE MCQ Model Questions — All Subjects (StudyNotesNepal)',
                     subject='English', format='pdf', section='College Model Questions',
                     size_label='5.6 MB', downloads=6100,
                     tags='["MCQ","Model Questions","All Subjects","Bridge Course"]',
                     file_url=REAL_LINKS['model_q']),
            Resource(title='Post-SEE Entrance Preparation Book — Gearing Up for +2 (Edusanjal Free PDF)',
                     subject='Mathematics', format='pdf', section='College Model Questions',
                     size_label='8.2 MB', downloads=5900,
                     tags='["Entrance","MCQ","Tips","Strategy","Free PDF","Edusanjal"]',
                     file_url=REAL_LINKS['edusanjal_book']),

            # Mathematics
            Resource(title='Mathematics Bridge Course Notes — Brighter Nepal (StudyNotesNepal)',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='14.2 MB', downloads=5100,
                     tags='["Mathematics","Calculus","Trigonometry","Bridge Course"]',
                     file_url=REAL_LINKS['math_bridge']),
            Resource(title='Integral Calculus: Definite & Indefinite — Brighter Nepal Notes 2081',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='11.6 MB', downloads=4700,
                     tags='["Calculus","Integration","Mathematics"]',
                     file_url=REAL_LINKS['math_bridge']),
            Resource(title='Differential Calculus: Limits, Derivatives & Applications',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='10.8 MB', downloads=4400,
                     tags='["Calculus","Differentiation","Limits"]',
                     file_url=REAL_LINKS['math_bridge'], live_class_id=_math_cls),
            Resource(title='Coordinate Geometry: Lines, Circles & Parabola — Brighter Nepal',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='9.6 MB', downloads=4100,
                     tags='["Coordinate Geometry","Lines","Circles"]',
                     file_url=REAL_LINKS['math_bridge']),
            Resource(title='Trigonometry: All Identities, Formulae & Solved Problems',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='8.8 MB', downloads=4300,
                     tags='["Trigonometry","Identities","Formulae"]',
                     file_url=REAL_LINKS['math_bridge'], live_class_id=_trig_cls),
            Resource(title='Permutations, Combinations & Probability — Brighter Nepal',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='6.4 MB', downloads=3800,
                     tags='["Probability","Permutations","Combinations"]',
                     file_url=REAL_LINKS['math_bridge']),
            Resource(title='Sets, Functions & Matrices — Brighter Nepal Math Notes 2081',
                     subject='Mathematics', format='pdf', section='Mathematics',
                     size_label='7.2 MB', downloads=3600,
                     tags='["Sets","Functions","Matrix","Determinants"]',
                     file_url=REAL_LINKS['math_bridge']),
            Resource(title='Integral Calculus Lecture Video — Er. Bikash Pokharel (Brighter Nepal)',
                     subject='Mathematics', format='video', section='Mathematics',
                     size_label='1:52:00', downloads=2900,
                     tags='["Calculus","Video","Lecture","YouTube","Brighter Nepal"]',
                     file_url=REAL_LINKS['bn_youtube']),
            Resource(title='Trigonometry Full Lecture — Er. Bikash Pokharel (Brighter Nepal YouTube)',
                     subject='Mathematics', format='video', section='Mathematics',
                     size_label='1:40:00', downloads=2600,
                     tags='["Trigonometry","Video","Lecture","YouTube","Brighter Nepal"]',
                     file_url=REAL_LINKS['bn_youtube'], live_class_id=_trig_cls),

            # Physics
            Resource(title='Physics Bridge Course Notes — Brighter Nepal (StudyNotesNepal)',
                     subject='Physics', format='pdf', section='Physics',
                     size_label='13.4 MB', downloads=5500,
                     tags='["Physics","Mechanics","Electricity","Optics","Bridge Course"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Mechanics: Motion, Forces, Work & Energy — Brighter Nepal Notes',
                     subject='Physics', format='pdf', section='Physics',
                     size_label='11.2 MB', downloads=5100,
                     tags='["Mechanics","Newton\'s Laws","Energy"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Light: Reflection, Refraction & Optical Instruments — Brighter Nepal',
                     subject='Physics', format='pdf', section='Physics',
                     size_label='10.4 MB', downloads=4900,
                     tags='["Optics","Light","Refraction","Reflection"]',
                     file_url=REAL_LINKS['physics_bridge'], live_class_id=_physics_cls),
            Resource(title='Electricity & Magnetism: Circuits & Electromagnetic Induction',
                     subject='Physics', format='pdf', section='Physics',
                     size_label='9.8 MB', downloads=4600,
                     tags='["Electricity","Magnetism","Circuits","Electromagnetism"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Heat, Thermodynamics & Kinetic Theory — Brighter Nepal Physics Notes',
                     subject='Physics', format='pdf', section='Physics',
                     size_label='8.6 MB', downloads=4300,
                     tags='["Thermodynamics","Heat","Kinetic Theory"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Modern Physics: Photoelectric Effect, X-Rays & Nuclear — Brighter Nepal',
                     subject='Physics', format='pdf', section='Physics',
                     size_label='9.0 MB', downloads=4100,
                     tags='["Modern Physics","Photoelectric Effect","Nuclear","Quantum"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Physics Formula Sheet — All Chapters Quick Reference (Brighter Nepal)',
                     subject='Physics', format='notes', section='Physics',
                     size_label='2.8 MB', downloads=6200,
                     tags='["Formula","Quick Reference","Physics","All Chapters"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Physics Video: Optics & Light — Er. Sanjaya Shrestha (Brighter Nepal)',
                     subject='Physics', format='video', section='Physics',
                     size_label='1:48:00', downloads=2700,
                     tags='["Optics","Video","Lecture","YouTube","Brighter Nepal"]',
                     file_url=REAL_LINKS['bn_youtube']),

            # Chemistry
            Resource(title='Chemistry Bridge Course Notes — Brighter Nepal (StudyNotesNepal)',
                     subject='Chemistry', format='pdf', section='Chemistry',
                     size_label='12.8 MB', downloads=5200,
                     tags='["Chemistry","Organic","Inorganic","Physical","Bridge Course"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Organic Chemistry: Aliphatic & Aromatic Compounds — Brighter Nepal',
                     subject='Chemistry', format='pdf', section='Chemistry',
                     size_label='13.4 MB', downloads=5000,
                     tags='["Organic Chemistry","Alkanes","Alkenes","Benzene"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Inorganic Chemistry: Periodic Table, Metals & Non-Metals',
                     subject='Chemistry', format='pdf', section='Chemistry',
                     size_label='10.6 MB', downloads=4500,
                     tags='["Inorganic Chemistry","Periodic Table","Metals"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Physical Chemistry: Atomic Structure, Bonding & Thermodynamics',
                     subject='Chemistry', format='pdf', section='Chemistry',
                     size_label='11.0 MB', downloads=4300,
                     tags='["Physical Chemistry","Atomic Structure","Thermodynamics"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Electrochemistry & Galvanic Cells — Brighter Nepal Quick Notes',
                     subject='Chemistry', format='notes', section='Chemistry',
                     size_label='4.2 MB', downloads=3800,
                     tags='["Electrochemistry","Galvanic","Electrolysis"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Chemical Equations & Reactions Chart — Quick Reference (Brighter Nepal)',
                     subject='Chemistry', format='notes', section='Chemistry',
                     size_label='2.4 MB', downloads=5100,
                     tags='["Reactions","Chemical Equations","Quick Reference"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Chemistry Lab Practical Guide: Techniques & Safety',
                     subject='Chemistry', format='pdf', section='Chemistry',
                     size_label='6.8 MB', downloads=3200,
                     tags='["Lab","Practical","Chemistry","Safety"]',
                     file_url=REAL_LINKS['chemistry_bridge']),

            # Biology — Zoology
            Resource(title='Zoology Bridge Course Notes — Cell Biology & Animal Kingdom (StudyNotesNepal)',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='14.4 MB', downloads=5600,
                     tags='["Zoology","Cell Biology","Animal Kingdom","Bridge Course"]',
                     file_url=REAL_LINKS['zoology_bridge']),
            Resource(title='Human Anatomy & Physiology — All Systems (Brighter Nepal)',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='13.0 MB', downloads=5200,
                     tags='["Human Anatomy","Physiology","Body Systems"]',
                     file_url=REAL_LINKS['zoology_bridge']),
            Resource(title="Genetics & Heredity: Mendel's Laws & DNA Structure — Brighter Nepal",
                     subject='Biology', format='pdf', section='Biology',
                     size_label='10.8 MB', downloads=4800,
                     tags='["Genetics","Heredity","DNA","Mendel"]',
                     file_url=REAL_LINKS['zoology_bridge']),
            Resource(title='Cell Division: Mitosis & Meiosis — Brighter Nepal Diagram Notes',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='8.6 MB', downloads=4600,
                     tags='["Cell Division","Mitosis","Meiosis","Diagrams"]',
                     file_url=REAL_LINKS['zoology_bridge']),

            # Biology — Botany
            Resource(title='Botany Bridge Course Notes — Plant Kingdom & Physiology (StudyNotesNepal)',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='12.2 MB', downloads=4800,
                     tags='["Botany","Plant Kingdom","Physiology","Bridge Course"]',
                     file_url=REAL_LINKS['botany_bridge']),
            Resource(title='Photosynthesis & Plant Nutrition — Brighter Nepal Notes',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='9.4 MB', downloads=4200,
                     tags='["Photosynthesis","Plant Nutrition","Chlorophyll"]',
                     file_url=REAL_LINKS['botany_bridge']),
            Resource(title='Flower Structure, Pollination & Seed Dispersal — Brighter Nepal',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='8.0 MB', downloads=3900,
                     tags='["Botany","Flowers","Pollination","Seed"]',
                     file_url=REAL_LINKS['botany_bridge']),

            # Biology — Ecology
            Resource(title='Ecology Bridge Course Notes — Ecosystems & Biodiversity (StudyNotesNepal)',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='9.8 MB', downloads=4000,
                     tags='["Ecology","Ecosystem","Biodiversity","Bridge Course"]',
                     file_url=REAL_LINKS['ecology_bridge']),
            Resource(title='Nepal Biodiversity & Conservation — Brighter Nepal Ecology Notes',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='7.6 MB', downloads=3600,
                     tags='["Nepal","Biodiversity","Conservation","IUCN"]',
                     file_url=REAL_LINKS['ecology_bridge']),
            Resource(title='Biology Diagram Practice Sheets — All Systems (Brighter Nepal)',
                     subject='Biology', format='pdf', section='Biology',
                     size_label='7.8 MB', downloads=4400,
                     tags='["Diagrams","Biology","Practice","All Systems"]',
                     file_url=REAL_LINKS['zoology_bridge']),
            Resource(title='Biology Video: Cell Division & Genetics — Dr. Kabita Adhikari (Brighter Nepal)',
                     subject='Biology', format='video', section='Biology',
                     size_label='1:32:00', downloads=3000,
                     tags='["Genetics","Cell Division","Video","Lecture","Brighter Nepal"]',
                     file_url=REAL_LINKS['bn_youtube']),

            # English
            Resource(title='English Bridge Course Notes — Grammar & Comprehension (StudyNotesNepal)',
                     subject='English', format='pdf', section='English',
                     size_label='9.4 MB', downloads=6000,
                     tags='["English","Grammar","Comprehension","Bridge Course"]',
                     file_url=REAL_LINKS['english_bridge']),
            Resource(title='English Grammar Complete Guide 2081 — Brighter Nepal',
                     subject='English', format='pdf', section='English',
                     size_label='10.2 MB', downloads=5800,
                     tags='["Grammar","Tenses","Voice","Narration","Sentence"]',
                     file_url=REAL_LINKS['english_bridge']),
            Resource(title='Vocabulary Builder: 3000 Key Words for +2 Entrance Exams',
                     subject='English', format='notes', section='English',
                     size_label='5.2 MB', downloads=5500,
                     tags='["Vocabulary","Words","Entrance","English"]',
                     file_url=REAL_LINKS['english_bridge']),
            Resource(title='Reading Comprehension Practice Sets (10 Passages) — Brighter Nepal',
                     subject='English', format='pdf', section='English',
                     size_label='6.8 MB', downloads=5000,
                     tags='["Comprehension","Reading","Passages","Practice"]',
                     file_url=REAL_LINKS['english_bridge']),
            Resource(title='Error Detection & Sentence Correction — Brighter Nepal English Notes',
                     subject='English', format='pdf', section='English',
                     size_label='5.4 MB', downloads=4700,
                     tags='["Error Detection","Sentence Correction","Grammar"]',
                     file_url=REAL_LINKS['english_bridge']),

            # Accountancy / Management
            Resource(title='Accountancy Basics for +2 Management — Brighter Nepal Notes 2081',
                     subject='Accountancy', format='pdf', section='Management',
                     size_label='11.4 MB', downloads=4200,
                     tags='["Accountancy","Journal","Ledger","Balance Sheet","Management"]',
                     file_url=REAL_LINKS['edusanjal_course']),
            Resource(title='Economics: Demand, Supply & Market Analysis — Management Batch',
                     subject='Economics', format='pdf', section='Management',
                     size_label='9.6 MB', downloads=3900,
                     tags='["Economics","Demand","Supply","Market","Management"]',
                     file_url=REAL_LINKS['edusanjal_course']),
            Resource(title='Business Mathematics: Algebra, Percentage & Interest — Management Batch',
                     subject='Mathematics', format='pdf', section='Management',
                     size_label='8.0 MB', downloads=3600,
                     tags='["Business Math","Percentage","Interest","Management"]',
                     file_url=REAL_LINKS['edusanjal_course']),

            # Extra Study Materials
            Resource(title='Advanced Maths Worksheet Pack (150 Problems) — Brighter Nepal',
                     subject='Mathematics', format='pdf', section='Extra Study Materials',
                     size_label='3.8 MB', downloads=4400,
                     tags='["Worksheet","Mathematics","Practice","150 Problems"]',
                     file_url=REAL_LINKS['math_bridge']),
            Resource(title='Physics Worksheet: 100 MCQ Practice Problems — Brighter Nepal',
                     subject='Physics', format='pdf', section='Extra Study Materials',
                     size_label='3.2 MB', downloads=4000,
                     tags='["Worksheet","Physics","MCQ","Practice"]',
                     file_url=REAL_LINKS['physics_bridge']),
            Resource(title='Biology Mind Maps — All Chapters (Brighter Nepal +2 Prep)',
                     subject='Biology', format='pdf', section='Extra Study Materials',
                     size_label='6.0 MB', downloads=4500,
                     tags='["Mind Maps","Biology","All Chapters","Quick Revision"]',
                     file_url=REAL_LINKS['zoology_bridge']),
            Resource(title='GK & Current Affairs for +2 Entrance Exams — Brighter Nepal 2081',
                     subject='GK', format='pdf', section='Extra Study Materials',
                     size_label='5.4 MB', downloads=4000,
                     tags='["GK","Current Affairs","Nepal","Entrance"]',
                     file_url=REAL_LINKS['edusanjal_book']),
            Resource(title='Exam Strategy & Time Management Guide — Brighter Nepal',
                     subject='English', format='notes', section='Extra Study Materials',
                     size_label='1.8 MB', downloads=3600,
                     tags='["Strategy","Exam Tips","Time Management","All Batches"]',
                     file_url=REAL_LINKS['edusanjal_book']),
            Resource(title='Chemistry Quick Reaction Chart — Organic & Inorganic (Brighter Nepal)',
                     subject='Chemistry', format='notes', section='Extra Study Materials',
                     size_label='2.2 MB', downloads=5000,
                     tags='["Chemistry","Reactions","Quick Reference","Chart"]',
                     file_url=REAL_LINKS['chemistry_bridge']),
            Resource(title='Brighter Nepal Online Bridge Course — Full Curriculum (Edusanjal)',
                     subject='Mathematics', format='video', section='Extra Study Materials',
                     size_label='Full Course', downloads=3100,
                     tags='["Online Course","Bridge Course","Edusanjal","All Subjects"]',
                     file_url=REAL_LINKS['edusanjal_course']),
            Resource(title='Brighter Nepal YouTube Channel — All Subject Lectures & Mock Tests',
                     subject='Mathematics', format='video', section='Extra Study Materials',
                     size_label='200+ Videos', downloads=8200,
                     tags='["YouTube","Video","All Subjects","Brighter Nepal","Free"]',
                     file_url=REAL_LINKS['bn_youtube']),
        ]
        db.session.add_all(resources)

        # ── Notices ───────────────────────────────────────────────────────────
        notices_data = [
            ('+2 Science Entrance Exam Dates 2081 — All Top Colleges Announced',
             "St. Xavier's (Chaitra 20), Budhanilkantha (Chaitra 22), SOS (Chaitra 25), Sainik Awasiya (Chaitra 28) and CCRC (Baisakh 2) entrance exam dates confirmed. All Brighter Nepal Science Batch students must complete admit card applications at admin desk by Falgun 28.",
             'urgent', 'Academic Affairs', REAL_LINKS['edusanjal_guide'], True, now - timedelta(hours=5)),
            ('Free Trial Access Ends Chaitra 30 — Upgrade to Full Plan',
             'All trial students: your 7-day free trial expires Chaitra 30, 2081. After that date, live classes, model sets and study materials are restricted. Upgrade at admin desk or via eSewa/Khalti to continue uninterrupted preparation.',
             'urgent', 'Admin Office', '#', True, now - timedelta(days=1)),
            ('Grand +2 Science Mock Exam — Falgun 25 (Compulsory)',
             'Compulsory Grand +2 Science Simulation Exam (90 min, 100 MCQs) on Falgun 25, 2081, at Brighter Nepal Main Exam Hall. Report by 6:45 AM. No entry after 7:05 AM. Bring student ID and pencil. Results published same evening.',
             'important', 'Examination Cell', '#', True, now - timedelta(days=2)),
            ('Grand +2 Management Mock Exam — Falgun 27 (Management Batch)',
             'Compulsory Grand Management Entrance Simulation (90 min, 75 MCQs) on Falgun 27, 2081. Accountancy, Economics, Business Maths, English & GK. Batch A at 8:00 AM, Batch B at 11:00 AM.',
             'important', 'Examination Cell', '#', False, now - timedelta(days=2)),
            ('Scholarship Test Results Published — Brighter Nepal 2081',
             'Results of the Brighter Nepal Internal Scholarship Test (Falgun 12) are published. 20 students receive fee waivers of 25–100%. Top scorer: Vivek Malla (Scholarship Batch) — 96/100. Check at admin desk or registered email.',
             'general', 'Academic Affairs', '#', False, now - timedelta(days=4)),
            ('Free PDF Added: Edusanjal Post-SEE Entrance Book',
             '"Gearing Up for +2 Entrance Exams" (Edusanjal) is now linked in Study Materials > College Model Questions. Covers strategy, MCQ techniques and all subjects. Download free — no login required.',
             'general', 'Content Team', REAL_LINKS['edusanjal_book'], False, now - timedelta(days=6)),
            ('StudyNotesNepal Bridge Course Notes — Now Linked in Study Materials',
             'All subject-wise bridge course notes from StudyNotesNepal.com (Physics, Chemistry, Maths, Biology, Ecology, English) are now directly linked. Free to access — click any resource in Study Materials.',
             'general', 'Content Team', REAL_LINKS['physics_bridge'], False, now - timedelta(days=7)),
            ('Parent-Teacher Meeting (PTM) — Falgun 28',
             'PTM for all batches on Falgun 28, 2081, from 10 AM to 2 PM. Guardians review ward performance with subject teachers. Compulsory for parents of trial-plan and scholarship batch students.',
             'general', 'Admin Office', '#', False, now - timedelta(days=9)),
            ('Brighter Nepal Annual Merit Ceremony — Chaitra 5, 2081',
             'Top-performing students from all batches honoured on Chaitra 5, 2081, at the Brighter Nepal Main Auditorium. Program at 11:00 AM. All students, parents and faculty invited.',
             'general', 'Admin Office', '#', False, now - timedelta(days=11)),
            ('Physics Lab Sessions — New Schedule for Science Batch',
             'Revised Physics Practical Lab session schedule for +2 Science Bridge Batch available at Science Lab desk (Ground Floor). First session: Falgun 22. Report in lab attire.',
             'general', 'Science Department', '#', False, now - timedelta(days=12)),
            ('New Batch Starting — +2 Science & Management (Post-SEE 2081)',
             'Registration open for next +2 Science and Management Bridge Course (Post-SEE 2081). Classes commence Baisakh 1, 2082. 15% early-bird discount until Chaitra 25. Limited seats — register early!',
             'important', 'Admissions', '#', False, now - timedelta(days=14)),
            ("Toppers' Strategy Session — Previous St. Xavier's & Budhanilkantha Toppers to Speak",
             "Brighter Nepal hosts a special Strategy Session featuring previous top scorers from St. Xavier's, Budhanilkantha & CCRC on Falgun 30. Open to all batches. Limited seats. Register at admin desk by Falgun 28.",
             'important', 'Academic Affairs', '#', False, now - timedelta(days=16)),
            ('Join Brighter Nepal Facebook Group — Resources & Daily Updates',
             'All students: join the official Brighter Nepal Facebook Group for daily notices, study tips, model questions and motivational content. Link on notice board and admin desk.',
             'general', 'Admin Office', REAL_LINKS['bn_facebook'], False, now - timedelta(days=18)),
            ('New Videos on Brighter Nepal YouTube Channel (@BRIGHTERNEPAL1)',
             'New lecture videos on Optics, Organic Chemistry and Trigonometry uploaded to Brighter Nepal YouTube. Subscribe and watch — completely free for all students.',
             'general', 'Content Team', REAL_LINKS['bn_youtube'], False, now - timedelta(days=20)),
        ]
        for nd in notices_data:
            n = Notice(title=nd[0], body=nd[1], category=nd[2],
                       department=nd[3], link_url=nd[4],
                       is_pinned=nd[5], created_at=nd[6])
            db.session.add(n)

        # ── Payments ──────────────────────────────────────────────────────────
        db.session.flush()
        pmethods  = ['eSewa', 'Khalti', 'Bank Transfer', 'IME Pay', 'fonePay', 'eSewa', 'Khalti']
        pstatuses = ['completed', 'completed', 'completed', 'completed', 'pending', 'failed', 'completed']

        def fee_for_group(gid):
            if gid == groups[0].id: return 7500.0   # +2 Science
            if gid == groups[1].id: return 5500.0   # +2 Management
            if gid == groups[2].id: return 9500.0   # A-Level Science
            if gid == groups[3].id: return 4500.0   # +2 Humanities
            if gid == groups[4].id: return 5000.0   # CTEVT
            return 8000.0                            # Scholarship Batch

        for i, student in enumerate(student_objs):
            db.session.add(Payment(
                user_id=student.id,
                amount=fee_for_group(student.group_id),
                method=pmethods[i % len(pmethods)],
                status=pstatuses[i % len(pstatuses)],
                created_at=now - timedelta(days=i * 4),
            ))

        # ── Group Messages ────────────────────────────────────────────────────
        db.session.flush()
        group_messages = [
            # +2 Science
            GroupMessage(group_id=groups[0].id, user_id=admin.id,
                         created_at=now - timedelta(hours=8),
                         text="🎓 Good morning, Brighter Nepal +2 Science Batch 2081! Mock Sets A, B & C for St. Xavier's, Budhanilkantha & SOS are now LIVE in Study Materials. Attempt all three before the Grand Mock on Falgun 25! 💪"),
            GroupMessage(group_id=groups[0].id, user_id=coordinator.id,
                         created_at=now - timedelta(hours=4),
                         text="📢 Tonight's LIVE class on Definite Integration by Er. Bikash sir starts at 7:00 PM sharp — covering all techniques with past entrance question practice. Don't miss it! 🔥"),
            GroupMessage(group_id=groups[0].id, user_id=faculty_objs[0].id,
                         created_at=now - timedelta(hours=1),
                         text="Hi Science Batch! The 150-problem Advanced Maths Worksheet is now in Study Materials. Do problems 1–50 before tomorrow and bring doubts to the QAD session. — Er. Bikash Pokharel"),
            GroupMessage(group_id=groups[0].id, user_id=faculty_objs[1].id,
                         created_at=now - timedelta(minutes=30),
                         text="Download the Physics Formula Sheet from Study Materials > Extra Materials. Memorize all highlighted formulae before the Grand Mock — especially Optics & Electricity! — Er. Sanjaya Shrestha"),
            # +2 Management
            GroupMessage(group_id=groups[1].id, user_id=admin.id,
                         created_at=now - timedelta(hours=7),
                         text="📊 Management Batch! Grand Mock on Falgun 27. Uniglobe, Sifal & Thames Mock Sets are now available. Revise Accountancy Chapters 1–8. Roshan sir reviews key journal entries tomorrow morning."),
            GroupMessage(group_id=groups[1].id, user_id=faculty_objs[5].id,
                         created_at=now - timedelta(hours=3),
                         text="Management students: Download Accountancy Basics notes from Study Materials > Management. Understand Double Entry — at least 15 marks in every management entrance comes from Accountancy! — Mr. Pawan Shrestha"),
            GroupMessage(group_id=groups[1].id, user_id=coordinator.id,
                         created_at=now - timedelta(hours=2),
                         text="📝 Weekly Test on Accountancy this Saturday — Journal, Ledger & Trial Balance (Chapters 1–5). Study the notes and attempt the practice MCQs in Study Materials. Good luck! 🙌"),
            # A-Level Science
            GroupMessage(group_id=groups[2].id, user_id=admin.id,
                         created_at=now - timedelta(hours=6),
                         text="🔬 A-Level Batch! Lincoln & Rato Bangala Mock Sets are live. A-Level entrance is concept-based — focus on application MCQs. Mr. Santosh sir's Physics session tomorrow 6:30 PM."),
            GroupMessage(group_id=groups[2].id, user_id=faculty_objs[7].id,
                         created_at=now - timedelta(hours=2),
                         text="A-Level Physics students: Work through the Physics Worksheet this weekend. Electricity and Modern Physics carry 40% of the A-Level entrance. Bring doubts Monday. — Mr. Santosh Gautam"),
            # +2 Humanities
            GroupMessage(group_id=groups[3].id, user_id=admin.id,
                         created_at=now - timedelta(hours=5),
                         text="📚 Humanities Batch! Weekly Test on Social Studies & English is Friday. Download GK & Current Affairs PDF from Study Materials > Extra Materials. Focus on Nepal history, geography and recent events."),
            GroupMessage(group_id=groups[3].id, user_id=faculty_objs[9].id,
                         created_at=now - timedelta(hours=2),
                         text="Today's session covers Nepal's federal system and local governance — high-frequency topics in humanities entrances. Check GK notes in Study Materials. — Mr. Kiran Timalsina"),
            # CTEVT
            GroupMessage(group_id=groups[4].id, user_id=admin.id,
                         created_at=now - timedelta(hours=4),
                         text="🏗️ CTEVT Batch! Diploma Entrance Mock Sets (Civil & Computer/Electrical) are live. Focus on basic Science, Maths & English. Naresh sir's session on Newton's Laws is tomorrow at 5 PM. 💡"),
            GroupMessage(group_id=groups[4].id, user_id=faculty_objs[10].id,
                         created_at=now - timedelta(hours=1),
                         text="CTEVT students: Download Physics Bridge Course Notes from Study Materials > Physics. Focus on Mechanics, Electricity & basic Chemistry for CTEVT entrance. 60 MCQs in 90 min — speed matters! — Mr. Naresh Bista"),
            # Scholarship Batch
            GroupMessage(group_id=groups[5].id, user_id=admin.id,
                         created_at=now - timedelta(hours=3),
                         text="🌟 Scholarship Batch! National Scholarship Practice Sets A & B are now available. Hard difficulty, 100 Qs. Your benchmark: 85+/100. Review with Er. Bikash sir on Wednesday evening."),
            GroupMessage(group_id=groups[5].id, user_id=coordinator.id,
                         created_at=now - timedelta(hours=1),
                         text="Today's Mock Test performance determines your seating rank for the Grand Simulation. Full marks puts you in the Toppers' Session on Falgun 30. Push hard this week! — Roshan Paudel"),
        ]
        db.session.add_all(group_messages)
        db.session.commit()

        print(
            f"\n✅  Brighter Nepal BridgeCourse seed complete!\n"
            f"   👥  {len(groups)} groups (all Bridge Course batches)\n"
            f"   👤  {2 + len(faculty_data) + len(student_objs)} users\n"
            f"   📚  {len(model_sets)} model sets "
            f"({sum(1 for m in model_sets if m.status=='published')} published, "
            f"{sum(1 for m in model_sets if m.status=='draft')} draft)\n"
            f"   📝  {len(tests)} weekly tests "
            f"({sum(1 for t in tests if t.status=='live')} live, "
            f"{sum(1 for t in tests if t.status=='scheduled')} scheduled, "
            f"{sum(1 for t in tests if t.status=='completed')} completed)\n"
            f"   ❓  {len(all_qs)} questions in bank:\n"
            f"       Maths:{len(math_qs)} | Physics:{len(physics_qs)} | Chem:{len(chemistry_qs)}\n"
            f"       Zoology:{len(zoology_qs)} | Botany:{len(botany_qs)} | Ecology:{len(ecology_qs)}\n"
            f"       English:{len(english_qs)} | GK:{len(gk_qs)} | Accountancy:{len(acc_qs)}\n"
            f"   📡  {len(classes)} live classes\n"
            f"   📄  {len(resources)} resources (with real working URLs)\n"
            f"   📢  {len(notices_data)} notices\n"
            f"   💳  {len(student_objs)} payments\n"
            f"   💬  {len(group_messages)} group messages\n"
            f"\n🔐  Admin:        admin@brighternepal.edu.np      / BrighterAdmin@2081\n"
            f"🔐  Coordinator:  coordinator@brighternepal.edu.np / BrighterAdmin@2081\n"
            f"🔐  Student:      aashish.maharjan@gmail.com       / Student@2081\n"
            f"\n🌐  Real resource links used:\n"
            f"    Physics notes:  {REAL_LINKS['physics_bridge']}\n"
            f"    Math notes:     {REAL_LINKS['math_bridge']}\n"
            f"    Chem notes:     {REAL_LINKS['chemistry_bridge']}\n"
            f"    English notes:  {REAL_LINKS['english_bridge']}\n"
            f"    Model Qs:       {REAL_LINKS['model_q']}\n"
            f"    Free PDF:       {REAL_LINKS['edusanjal_book']}\n"
            f"    YouTube:        {REAL_LINKS['bn_youtube']}\n"
        )


if __name__ == '__main__':
    seed()