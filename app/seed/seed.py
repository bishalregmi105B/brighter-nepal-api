"""
Seed script — Brighter Nepal Bridgecourse Preparation Institute
Realistic demo data: IOE / IOM / CSIT / +2 Science / +2 Management batches.
Run: python app/seed/seed.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app import create_app, db
from app.models import (
    User, Group, ModelSet, WeeklyTest, WeeklyTestQuestion,
    LiveClass, Resource, Notice, Payment, GroupMessage
)
from datetime import datetime, timedelta
import json

app = create_app()


def seed():
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Tables created.")

        # ── Groups ───────────────────────────────────────────────────────────
        groups = [
            Group(
                name='Brighter Nepal — IOE Engineering Batch 2081',
                description='Official IOE entrance preparation group — Brighter Nepal. Covers Physics, Chemistry, Mathematics & English for TU/IOE, KU, PU & PoU entrance exams.',
                member_count=420,
            ),
            Group(
                name='Brighter Nepal — IOM/CEE Medical Batch 2081',
                description='CEE/IOM MBBS & BDS entrance preparation. Focused on Physics, Chemistry, Biology & English for medical aspirants.',
                member_count=310,
            ),
            Group(
                name='Brighter Nepal — CSIT & BIT Entrance Batch 2081',
                description='B.Sc. CSIT and BIT entrance preparation covering Mathematics, Physics, and Computer Fundamentals.',
                member_count=195,
            ),
            Group(
                name='Brighter Nepal — +2 Science Bridge Course (NEB) 2081',
                description='Advanced Science Bridge Course for SEE-appeared students. Prepares for NEB +2 Grade 11 curriculum and college entrance exams — St. Xavier\'s, Budhanilkantha, SOS & KMC.',
                member_count=540,
            ),
            Group(
                name='Brighter Nepal — +2 Management Bridge Course 2081',
                description='Advanced Management Bridge Course for SEE-appeared students targeting leading management colleges across Nepal.',
                member_count=230,
            ),
            Group(
                name='Brighter Nepal — Staff Nurse & Paramedical Batch 2081',
                description='Entrance preparation for B.Sc. Nursing, Staff Nurse, HA, Lab Technician and CTEVT paramedical programs.',
                member_count=160,
            ),
        ]
        db.session.add_all(groups)
        db.session.flush()

        # ── Admin / Staff Users ───────────────────────────────────────────────
        admin = User(
            name='Brighter Nepal Admin',
            email='admin@brighternepal.edu.np',
            plan='paid', status='active', role='admin',
            group_id=groups[0].id,
        )
        admin.set_password('BrighterAdmin@2081')
        admin.on_login()  # initialise session_token so JWT validation works from first login
        db.session.add(admin)

        coordinator = User(
            name='Roshan Paudel',
            email='coordinator@brighternepal.edu.np',
            plan='paid', status='active', role='admin',
            group_id=groups[0].id,
        )
        coordinator.set_password('BrighterAdmin@2081')
        coordinator.on_login()
        db.session.add(coordinator)

        # Faculty accounts (admin role)
        faculty_data = [
            ('Er. Bikash Pokharel',    'bikash.pokharel@brighternepal.edu.np',    groups[0].id),   # Maths / IOE
            ('Er. Sanjaya Shrestha',   'sanjaya.shrestha@brighternepal.edu.np',   groups[0].id),   # Physics / IOE
            ('Dr. Kabita Adhikari',    'kabita.adhikari@brighternepal.edu.np',    groups[1].id),   # Biology / IOM
            ('Mr. Dipendra Karki',     'dipendra.karki@brighternepal.edu.np',     groups[0].id),   # Chemistry
            ('Ms. Sunita Thapa',       'sunita.thapa@brighternepal.edu.np',       groups[3].id),   # English
            ('Er. Nabin Acharya',      'nabin.acharya@brighternepal.edu.np',      groups[2].id),   # Computer / CSIT
            ('Dr. Rajan Ghimire',      'rajan.ghimire@brighternepal.edu.np',      groups[1].id),   # Chemistry / IOM
        ]
        faculty_objs = []
        for fname, femail, fgid in faculty_data:
            fu = User(name=fname, email=femail, plan='paid', status='active', role='admin', group_id=fgid)
            fu.set_password('BrighterAdmin@2081')
            fu.on_login()
            db.session.add(fu)
            faculty_objs.append(fu)

        # ── Students ─────────────────────────────────────────────────────────
        students_data = [
            # IOE batch
            ('Aashish Maharjan',      'aashish.maharjan@gmail.com',       'paid',  groups[0].id),
            ('Barsha Pandit',         'barsha.pandit@gmail.com',          'paid',  groups[0].id),
            ('Bishal Thapa Magar',    'bishal.thapamagar@gmail.com',      'trial', groups[0].id),
            ('Dibya Shrestha',        'dibya.shrestha@gmail.com',         'paid',  groups[0].id),
            ('Gagan Bista',           'gagan.bista@gmail.com',            'paid',  groups[0].id),
            ('Hema Rana',             'hema.rana@gmail.com',              'trial', groups[0].id),
            ('Ishan Baral',           'ishan.baral@gmail.com',            'paid',  groups[0].id),
            ('Jyoti Khanal',          'jyoti.khanal@gmail.com',           'paid',  groups[0].id),
            ('Kamal Dhungana',        'kamal.dhungana@gmail.com',         'paid',  groups[0].id),
            ('Laxmi Paudel',          'laxmi.paudel@gmail.com',           'trial', groups[0].id),
            ('Milan Chaudhary',       'milan.chaudhary@gmail.com',        'paid',  groups[0].id),
            ('Nisha Lamichhane',      'nisha.lamichhane@gmail.com',       'paid',  groups[0].id),
            ('Om Prakash Dhakal',     'omprakash.dhakal@gmail.com',       'trial', groups[0].id),
            ('Prajwal Acharya',       'prajwal.acharya@gmail.com',        'paid',  groups[0].id),
            ('Rakshya Gurung',        'rakshya.gurung@gmail.com',         'paid',  groups[0].id),
            # IOM batch
            ('Samiksha Bhattarai',    'samiksha.bhattarai@gmail.com',     'paid',  groups[1].id),
            ('Sujan Kafle',           'sujan.kafle@gmail.com',            'paid',  groups[1].id),
            ('Tanisha Rai',           'tanisha.rai@gmail.com',            'trial', groups[1].id),
            ('Ujjwal Koirala',        'ujjwal.koirala@gmail.com',         'paid',  groups[1].id),
            ('Yamuna Subedi',         'yamuna.subedi@gmail.com',          'paid',  groups[1].id),
            ('Anil Tamang',           'anil.tamang@gmail.com',            'trial', groups[1].id),
            ('Bimala Sapkota',        'bimala.sapkota@gmail.com',         'paid',  groups[1].id),
            ('Chandra Prasad Oli',    'chandraprasad.oli@gmail.com',      'paid',  groups[1].id),
            ('Dipika Magar',          'dipika.magar@gmail.com',           'trial', groups[1].id),
            ('Elina Basnet',          'elina.basnet@gmail.com',           'paid',  groups[1].id),
            # CSIT batch
            ('Faizan Ansari',         'faizan.ansari@gmail.com',          'paid',  groups[2].id),
            ('Garima Thapa',          'garima.thapa@gmail.com',           'paid',  groups[2].id),
            ('Hari Bahadur Saud',     'hari.saud@gmail.com',              'trial', groups[2].id),
            ('Indira Sharma',         'indira.sharma@gmail.com',          'paid',  groups[2].id),
            ('Jayendra Budhathoki',   'jayendra.budhathoki@gmail.com',    'paid',  groups[2].id),
            # +2 Science Bridge Course
            ('Kritika Pokhrel',       'kritika.pokhrel@gmail.com',        'paid',  groups[3].id),
            ('Lokendra Bhandari',     'lokendra.bhandari@gmail.com',      'paid',  groups[3].id),
            ('Manisha Neupane',       'manisha.neupane@gmail.com',        'trial', groups[3].id),
            ('Niruta Giri',           'niruta.giri@gmail.com',            'paid',  groups[3].id),
            ('Paras Shrestha',        'paras.shrestha@gmail.com',         'paid',  groups[3].id),
            ('Roshani Dahal',         'roshani.dahal@gmail.com',          'trial', groups[3].id),
            ('Suman Ghimire',         'suman.ghimire@gmail.com',          'paid',  groups[3].id),
            ('Trishna Kc',            'trishna.kc@gmail.com',             'paid',  groups[3].id),
            # +2 Management Bridge Course
            ('Umesh Prajapati',       'umesh.prajapati@gmail.com',        'paid',  groups[4].id),
            ('Vibha Joshi',           'vibha.joshi@gmail.com',            'trial', groups[4].id),
            ('Asmita Rawat',          'asmita.rawat@gmail.com',           'paid',  groups[4].id),
            ('Bikram Tharu',          'bikram.tharu@gmail.com',           'paid',  groups[4].id),
            # Staff Nurse / Paramedical
            ('Chandrika Adhikari',    'chandrika.adhikari@gmail.com',     'paid',  groups[5].id),
            ('Deepa Lama',            'deepa.lama@gmail.com',             'trial', groups[5].id),
            ('Esha Rijal',            'esha.rijal@gmail.com',             'paid',  groups[5].id),
            ('Farmila Miya',          'farmila.miya@gmail.com',           'paid',  groups[5].id),
        ]
        student_objs = []
        for name, email, plan, gid in students_data:
            u = User(name=name, email=email, plan=plan, status='active', role='student', group_id=gid)
            u.set_password('Student@2081')
            u.on_login()  # set session_token so single-device enforcement works from login
            db.session.add(u)
            student_objs.append(u)
        db.session.flush()

        # ── Model Sets ────────────────────────────────────────────────────────
        model_sets = [
            # IOE Engineering sets
            ModelSet(title='IOE Entrance Full Mock — Set A (Brighter Nepal 2081)',        difficulty='Medium', duration_min=120, total_questions=100, status='published', targets='["IOE"]'),
            ModelSet(title='IOE Entrance Full Mock — Set B (Brighter Nepal 2081)',        difficulty='Hard',   duration_min=120, total_questions=100, status='published', targets='["IOE"]'),
            ModelSet(title='IOE Entrance Full Mock — Set C (Brighter Nepal 2081)',        difficulty='Hard',   duration_min=120, total_questions=100, status='published', targets='["IOE"]'),
            ModelSet(title='Pulchowk Campus Special Mock — Brighter Nepal 2081',         difficulty='Hard',   duration_min=120, total_questions=100, status='published', targets='["IOE"]'),
            ModelSet(title='Thapathali Engineering Mock — Brighter Nepal 2081',           difficulty='Medium', duration_min=120, total_questions=100, status='published', targets='["IOE"]'),
            ModelSet(title='Kathmandu University (KU) Engineering Mock 2081',            difficulty='Hard',   duration_min=120, total_questions=100, status='published', targets='["IOE","KU"]'),
            ModelSet(title='Pokhara University Engineering Entrance Mock 2081',          difficulty='Medium', duration_min=120, total_questions=100, status='published', targets='["IOE","PU"]'),
            ModelSet(title='IOE Physics Focus Mock — Brighter Nepal',                    difficulty='Medium', duration_min=90,  total_questions=75,  status='published', targets='["IOE"]'),
            ModelSet(title='IOE Mathematics Deep Dive Mock — Brighter Nepal',            difficulty='Hard',   duration_min=90,  total_questions=75,  status='published', targets='["IOE"]'),
            ModelSet(title='IOE Chemistry & English Practice Set — Brighter Nepal',      difficulty='Easy',   duration_min=60,  total_questions=50,  status='published', targets='["IOE"]'),
            # IOM / CEE Medical sets
            ModelSet(title='CEE Medical Full Mock — Set A (Brighter Nepal 2081)',        difficulty='Hard',   duration_min=180, total_questions=200, status='published', targets='["IOM","CEE"]'),
            ModelSet(title='CEE Medical Full Mock — Set B (Brighter Nepal 2081)',        difficulty='Hard',   duration_min=180, total_questions=200, status='published', targets='["IOM","CEE"]'),
            ModelSet(title='CEE Medical Full Mock — Set C (Brighter Nepal 2081)',        difficulty='Hard',   duration_min=180, total_questions=200, status='published', targets='["IOM","CEE"]'),
            ModelSet(title='IOM MBBS Entrance Special Mock — Brighter Nepal',           difficulty='Hard',   duration_min=180, total_questions=200, status='published', targets='["IOM"]'),
            ModelSet(title='BPKIHS & B.Sc. Nursing Entrance Mock 2081',                 difficulty='Medium', duration_min=120, total_questions=100, status='published', targets='["IOM","Nursing"]'),
            ModelSet(title='CEE Biology Intensive Mock — Brighter Nepal',               difficulty='Medium', duration_min=90,  total_questions=80,  status='published', targets='["IOM","CEE"]'),
            # CSIT / BIT
            ModelSet(title='B.Sc. CSIT Entrance Mock — Set A (Brighter Nepal 2081)',    difficulty='Medium', duration_min=90,  total_questions=75,  status='published', targets='["CSIT"]'),
            ModelSet(title='B.Sc. CSIT Entrance Mock — Set B (Brighter Nepal 2081)',    difficulty='Hard',   duration_min=90,  total_questions=75,  status='published', targets='["CSIT"]'),
            ModelSet(title='BIT Entrance Mock — Brighter Nepal 2081',                   difficulty='Medium', duration_min=90,  total_questions=75,  status='published', targets='["CSIT","BIT"]'),
            # +2 Bridge Course Entrance
            ModelSet(title='St. Xavier\'s College Entrance Mock — Brighter Nepal 2081', difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["StXaviers","+2"]'),
            ModelSet(title='Budhanilkantha School Entrance Mock — Brighter Nepal',      difficulty='Hard',   duration_min=90,  total_questions=100, status='published', targets='["Budhanilkantha","+2"]'),
            ModelSet(title='SOS Hermann Gmeiner School Entrance Mock 2081',             difficulty='Medium', duration_min=90,  total_questions=100, status='published', targets='["SOS","+2"]'),
            ModelSet(title='KMC / NIST / Prasadi Entrance Combined Mock 2081',          difficulty='Medium', duration_min=90,  total_questions=100, status='published', targets='["+2","KMC","NIST"]'),
            # Paramedical / Nursing
            ModelSet(title='Staff Nurse & B.Sc. Nursing Entrance Mock 2081',            difficulty='Medium', duration_min=120, total_questions=100, status='published', targets='["Nursing","CTEVT"]'),
            ModelSet(title='HA & Lab Technician Entrance Mock 2081',                    difficulty='Easy',   duration_min=90,  total_questions=75,  status='published', targets='["CTEVT","HA"]'),
            # Drafts / upcoming
            ModelSet(title='IOE Grand Final Mock — 72-hr Before Exam Set 2081',         difficulty='Hard',   duration_min=120, total_questions=100, status='draft',     targets='["IOE"]'),
            ModelSet(title='CEE Grand Final Mock — 72-hr Before Exam Set 2081',         difficulty='Hard',   duration_min=180, total_questions=200, status='draft',     targets='["IOM","CEE"]'),
        ]
        db.session.add_all(model_sets)

        # ── Weekly Tests ──────────────────────────────────────────────────────
        now = datetime.utcnow()
        tests = [
            # Live
            WeeklyTest(title='Brighter Nepal Weekly Test — Definite & Indefinite Integration',  subject='Mathematics', duration_min=60, status='live',      scheduled_at=now),
            # Upcoming
            WeeklyTest(title='Brighter Nepal Weekly Test — Electromagnetic Induction & AC',      subject='Physics',     duration_min=45, status='scheduled', scheduled_at=now + timedelta(days=1)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Organic Chemistry (Hydrocarbons)',     subject='Chemistry',   duration_min=60, status='scheduled', scheduled_at=now + timedelta(days=3)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Cell Division & Genetics',             subject='Biology',     duration_min=50, status='scheduled', scheduled_at=now + timedelta(days=5)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Computer Architecture & OS Basics',   subject='Computer',    duration_min=40, status='scheduled', scheduled_at=now + timedelta(days=6)),
            WeeklyTest(title='Brighter Nepal Weekly Test — English Grammar & Reading Comprehension', subject='English',  duration_min=30, status='scheduled', scheduled_at=now + timedelta(days=8)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Coordinate Geometry & Vectors',       subject='Mathematics', duration_min=60, status='scheduled', scheduled_at=now + timedelta(days=10)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Thermodynamics & Heat Transfer',      subject='Physics',     duration_min=45, status='scheduled', scheduled_at=now + timedelta(days=12)),
            # Completed
            WeeklyTest(title='Brighter Nepal Weekly Test — Differential Equations',              subject='Mathematics', duration_min=60, status='completed', scheduled_at=now - timedelta(days=3)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Optics & Wave Optics',                subject='Physics',     duration_min=45, status='completed', scheduled_at=now - timedelta(days=7)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Chemical Bonding & Periodicity',      subject='Chemistry',   duration_min=60, status='completed', scheduled_at=now - timedelta(days=10)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Human Physiology (Cardio)',           subject='Biology',     duration_min=50, status='completed', scheduled_at=now - timedelta(days=14)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Permutation & Combination',           subject='Mathematics', duration_min=45, status='completed', scheduled_at=now - timedelta(days=17)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Gravitation & Circular Motion',       subject='Physics',     duration_min=45, status='completed', scheduled_at=now - timedelta(days=21)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Electrochemistry & Galvanic Cells',   subject='Chemistry',   duration_min=60, status='completed', scheduled_at=now - timedelta(days=24)),
            WeeklyTest(title='Brighter Nepal Weekly Test — Ecology & Biodiversity',              subject='Biology',     duration_min=45, status='completed', scheduled_at=now - timedelta(days=28)),
        ]
        db.session.add_all(tests)
        db.session.flush()

        # Sample questions — live Integration test
        integration_questions = [
            ('Evaluate: ∫(3x² + 2x − 5) dx',                                  ['x³ + x² − 5x + C', 'x³ + x² + 5x + C', '6x + 2 + C', '3x³ + 2x² − 5x + C'], 0),
            ('What is ∫sin(x) dx?',                                             ['−cos(x) + C', 'cos(x) + C', 'sec(x) + C', 'tan(x) + C'], 0),
            ('Evaluate ∫₀² x³ dx.',                                             ['4', '8', '2', '16'], 0),
            ('Which method is used for ∫x·eˣ dx?',                             ['Integration by Parts', 'Substitution', 'Partial Fractions', 'Direct Integration'], 0),
            ('Find ∫(1/x) dx for x > 0.',                                       ['ln|x| + C', '1/x² + C', 'x + C', '−1/x + C'], 0),
            ('Evaluate ∫cos²(x) dx using the half-angle formula.',              ['x/2 + sin(2x)/4 + C', 'sin²(x) + C', 'x + C', 'cos(x)sin(x) + C'], 0),
            ('The area under y = x² from x = 0 to x = 3 is:',                  ['9', '27', '3', '6'], 0),
            ('∫eˣ cos(x) dx requires which technique?',                         ['Integration by Parts (twice)', 'Substitution', 'Standard formula', 'Partial fractions'], 0),
            ('If F(x) = ∫₁ˣ t² dt, then F\'(x) = ?',                           ['x²', '2x', '1', 'x³/3'], 0),
            ('Evaluate ∫(2x+3)⁵ dx using substitution.',                       ['(2x+3)⁶/12 + C', '(2x+3)⁶/6 + C', '5(2x+3)⁴ + C', '(2x+3)⁶ + C'], 0),
        ]

        # Physics EM questions (upcoming test 2 — pre-populate)
        em_questions = [
            ('Faraday\'s law relates EMF to the rate of change of:',            ['Magnetic flux', 'Electric flux', 'Current', 'Voltage'], 0),
            ('The SI unit of magnetic flux is:',                                 ['Weber (Wb)', 'Tesla (T)', 'Henry (H)', 'Ampere (A)'], 0),
            ('Lenz\'s law is a consequence of conservation of:',                ['Energy', 'Charge', 'Momentum', 'Mass'], 0),
            ('In a transformer, if Np/Ns = 10, the voltage ratio Vs/Vp is:',   ['0.1', '10', '1', '100'], 0),
            ('Self-inductance of a coil is measured in:',                       ['Henry (H)', 'Farad (F)', 'Ohm (Ω)', 'Tesla (T)'], 0),
        ]

        for text, options, ans_idx in integration_questions:
            db.session.add(WeeklyTestQuestion(test_id=tests[0].id, text=text, options=json.dumps(options), answer_index=ans_idx))

        for text, options, ans_idx in em_questions:
            db.session.add(WeeklyTestQuestion(test_id=tests[1].id, text=text, options=json.dumps(options), answer_index=ans_idx))

        # Organic Chemistry questions (test 3)
        organic_questions = [
            ('Alkanes follow the general formula:',                             ['CₙH₂ₙ₊₂', 'CₙH₂ₙ', 'CₙH₂ₙ₋₂', 'CₙHₙ'], 0),
            ('The IUPAC name of CH₃−CH₂−CH₂−CH₃ is:',                        ['Butane', 'Propane', 'Pentane', 'Methane'], 0),
            ('Which reaction converts alkene to alkane?',                       ['Hydrogenation', 'Halogenation', 'Combustion', 'Dehydration'], 0),
            ('Benzene undergoes primarily which type of reaction?',             ['Electrophilic substitution', 'Nucleophilic addition', 'Free-radical addition', 'Elimination'], 0),
            ('Markovnikov\'s rule applies to addition reactions of:',           ['Alkenes', 'Alkanes', 'Alkynes only', 'Benzene'], 0),
        ]
        for text, options, ans_idx in organic_questions:
            db.session.add(WeeklyTestQuestion(test_id=tests[2].id, text=text, options=json.dumps(options), answer_index=ans_idx))

        # Cell Biology questions (test 4)
        bio_questions = [
            ('DNA replication is described as:',                                ['Semi-conservative', 'Conservative', 'Dispersive', 'Asymmetric'], 0),
            ('Which organelle is called the "powerhouse of the cell"?',        ['Mitochondria', 'Ribosome', 'Golgi apparatus', 'Lysosome'], 0),
            ('Meiosis results in:',                                             ['4 haploid cells', '2 diploid cells', '4 diploid cells', '2 haploid cells'], 0),
            ('The law of segregation was proposed by:',                        ['Gregor Mendel', 'Charles Darwin', 'Louis Pasteur', 'Watson & Crick'], 0),
            ('Which base pairs with Thymine in DNA?',                          ['Adenine', 'Guanine', 'Cytosine', 'Uracil'], 0),
        ]
        for text, options, ans_idx in bio_questions:
            db.session.add(WeeklyTestQuestion(test_id=tests[3].id, text=text, options=json.dumps(options), answer_index=ans_idx))

        # Computer fundamentals (test 5)
        cs_questions = [
            ('Which generation of computers used transistors?',                ['Second', 'First', 'Third', 'Fourth'], 0),
            ('In binary, 1010₂ equals decimal:',                              ['10', '8', '12', '5'], 0),
            ('The full form of ALU is:',                                       ['Arithmetic Logic Unit', 'Array Logic Unit', 'Arithmetic Linear Unit', 'Analog Logic Unit'], 0),
            ('Which memory is volatile?',                                      ['RAM', 'ROM', 'Hard disk', 'Flash drive'], 0),
            ('An operating system is a type of:',                              ['System software', 'Application software', 'Utility software', 'Firmware'], 0),
        ]
        for text, options, ans_idx in cs_questions:
            db.session.add(WeeklyTestQuestion(test_id=tests[4].id, text=text, options=json.dumps(options), answer_index=ans_idx))

        # ── Live Classes ──────────────────────────────────────────────────────
        classes = [
            # Live now
            LiveClass(title='Definite Integration: Techniques & IOE 2075–2081 Past Questions',         teacher='Er. Bikash Pokharel (Brighter Nepal)', subject='Mathematics', duration_min=90,  status='live',      watchers=3100, scheduled_at=now),
            # Upcoming
            LiveClass(title='Electromagnetic Induction — Faraday, Lenz & Transformer Problems',        teacher='Er. Sanjaya Shrestha (Brighter Nepal)', subject='Physics',     duration_min=75,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(hours=3)),
            LiveClass(title='Aliphatic Compounds: Alkanes, Alkenes & Alkynes — IOE Focus',             teacher='Mr. Dipendra Karki (Brighter Nepal)',   subject='Chemistry',   duration_min=80,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(hours=6)),
            LiveClass(title='Cell Division: Mitosis vs Meiosis — CEE Level Deep Dive',                 teacher='Dr. Kabita Adhikari (Brighter Nepal)',  subject='Biology',     duration_min=60,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(hours=10)),
            LiveClass(title='Coordinate Geometry: Straight Lines & Circles — IOE Past Questions',      teacher='Er. Bikash Pokharel (Brighter Nepal)',  subject='Mathematics', duration_min=90,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=2)),
            LiveClass(title='Thermodynamics: Laws, Heat Engine & Carnot Cycle — IOE/IOM Prep',        teacher='Er. Sanjaya Shrestha (Brighter Nepal)', subject='Physics',     duration_min=75,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=3)),
            LiveClass(title='Organic Chemistry: Aromatic Compounds & Reactions — CEE Focused',        teacher='Dr. Rajan Ghimire (Brighter Nepal)',    subject='Chemistry',   duration_min=80,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=4)),
            LiveClass(title='Human Cardiorespiratory System — IOM/CEE Biology Session',               teacher='Dr. Kabita Adhikari (Brighter Nepal)',  subject='Biology',     duration_min=60,  status='upcoming',  watchers=0, scheduled_at=now + timedelta(days=5)),
            LiveClass(title='CSIT Entrance Prep: Data Structures & Algorithm Basics',                  teacher='Er. Nabin Acharya (Brighter Nepal)',    subject='Computer',    duration_min=90,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=6)),
            LiveClass(title='English: Comprehension, Grammar & Technical Writing for IOE',             teacher='Ms. Sunita Thapa (Brighter Nepal)',     subject='English',     duration_min=60,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=7)),
            LiveClass(title='Permutations, Combinations & Probability — IOE/CSIT',                    teacher='Er. Bikash Pokharel (Brighter Nepal)',  subject='Mathematics', duration_min=90,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=9)),
            LiveClass(title='Electrochemistry & Electrolysis — IOE/IOM/CEE Combined Session',         teacher='Mr. Dipendra Karki (Brighter Nepal)',   subject='Chemistry',   duration_min=75,  status='locked',    watchers=0, scheduled_at=now + timedelta(days=10)),
            # Completed
            LiveClass(title='Differential Calculus: Limits, Continuity & Differentiation',            teacher='Er. Bikash Pokharel (Brighter Nepal)',  subject='Mathematics', duration_min=100, status='completed', watchers=0, scheduled_at=now - timedelta(days=4)),
            LiveClass(title='Optics: Reflection, Refraction & Total Internal Reflection — IOE Level', teacher='Er. Sanjaya Shrestha (Brighter Nepal)', subject='Physics',     duration_min=110, status='completed', watchers=0, scheduled_at=now - timedelta(days=7)),
            LiveClass(title='Chemical Kinetics & Equilibrium — CEE/IOE Focused Session',              teacher='Dr. Rajan Ghimire (Brighter Nepal)',    subject='Chemistry',   duration_min=90,  status='completed', watchers=0, scheduled_at=now - timedelta(days=10)),
            LiveClass(title='Ecology, Biodiversity & Conservation Biology — CEE 2081',                teacher='Dr. Kabita Adhikari (Brighter Nepal)',  subject='Biology',     duration_min=75,  status='completed', watchers=0, scheduled_at=now - timedelta(days=13)),
            LiveClass(title='Vectors, 3D Geometry & Planes — IOE Mathematics Session',                teacher='Er. Bikash Pokharel (Brighter Nepal)',  subject='Mathematics', duration_min=105, status='completed', watchers=0, scheduled_at=now - timedelta(days=16)),
            LiveClass(title='Current Electricity & Kirchhoff\'s Laws — IOE Physics',                  teacher='Er. Sanjaya Shrestha (Brighter Nepal)', subject='Physics',     duration_min=90,  status='completed', watchers=0, scheduled_at=now - timedelta(days=20)),
            LiveClass(title='Gaseous State, Solid State & Solutions — IOE/IOM Chemistry',             teacher='Mr. Dipendra Karki (Brighter Nepal)',   subject='Chemistry',   duration_min=80,  status='completed', watchers=0, scheduled_at=now - timedelta(days=23)),
            LiveClass(title='Human Nervous System & Sense Organs — IOM/CEE Deep Dive',               teacher='Dr. Kabita Adhikari (Brighter Nepal)',  subject='Biology',     duration_min=70,  status='completed', watchers=0, scheduled_at=now - timedelta(days=27)),
            LiveClass(title='Computer Networks & Internet — CSIT Entrance Preparation',               teacher='Er. Nabin Acharya (Brighter Nepal)',    subject='Computer',    duration_min=75,  status='completed', watchers=0, scheduled_at=now - timedelta(days=30)),
            LiveClass(title='English Vocabulary Building & Error Detection — IOE Session',            teacher='Ms. Sunita Thapa (Brighter Nepal)',     subject='English',     duration_min=60,  status='completed', watchers=0, scheduled_at=now - timedelta(days=34)),
        ]
        db.session.add_all(classes)

        # ── Resources ─────────────────────────────────────────────────────────
        resources = [
            # Past Papers — College Model Questions
            Resource(title='IOE Entrance 2080 Full Paper with Solutions — Brighter Nepal',              subject='Mathematics', format='pdf',   section='College Model Questions',  size_label='7.2 MB',  downloads=6400, tags='["IOE","Past Paper","2080","Solutions"]'),
            Resource(title='IOE Entrance 2079 Full Paper with Solutions — Brighter Nepal',              subject='Physics',     format='pdf',   section='College Model Questions',  size_label='6.8 MB',  downloads=5900, tags='["IOE","Past Paper","2079","Solutions"]'),
            Resource(title='IOE Entrance 2078 Full Paper with Solutions — Brighter Nepal',              subject='Chemistry',   format='pdf',   section='College Model Questions',  size_label='6.1 MB',  downloads=5500, tags='["IOE","Past Paper","2078","Solutions"]'),
            Resource(title='IOE Entrance 2077 Full Paper with Solutions — Brighter Nepal',              subject='Mathematics', format='pdf',   section='College Model Questions',  size_label='5.8 MB',  downloads=4800, tags='["IOE","Past Paper","2077","Solutions"]'),
            Resource(title='CEE Medical 2080 Full Paper (Brighter Nepal Analysis)',                     subject='Biology',     format='pdf',   section='College Model Questions',  size_label='8.5 MB',  downloads=5200, tags='["IOM","CEE","Past Paper","2080"]'),
            Resource(title='CEE Medical 2079 Full Paper (Brighter Nepal Analysis)',                     subject='Biology',     format='pdf',   section='College Model Questions',  size_label='8.0 MB',  downloads=4700, tags='["IOM","CEE","Past Paper","2079"]'),
            Resource(title='Pulchowk Campus Special Mock 2081 — Full Set',                             subject='Mathematics', format='pdf',   section='College Model Questions',  size_label='9.0 MB',  downloads=4200, tags='["IOE","Mock","Pulchowk","2081"]'),
            Resource(title='Thapathali Engineering Mock 2081 — Full Set',                              subject='Mathematics', format='pdf',   section='College Model Questions',  size_label='8.2 MB',  downloads=3800, tags='["IOE","Mock","Thapathali","2081"]'),
            Resource(title='KU Engineering Entrance 2080 Paper — Brighter Nepal',                      subject='Physics',     format='pdf',   section='College Model Questions',  size_label='7.5 MB',  downloads=3100, tags='["KU","Engineering","2080"]'),
            Resource(title='St. Xavier\'s +2 Science Entrance 2081 Mock — Brighter Nepal',            subject='Mathematics', format='pdf',   section='College Model Questions',  size_label='5.5 MB',  downloads=3500, tags='["+2","StXaviers","Entrance","2081"]'),
            Resource(title='Budhanilkantha School Entrance Mock 2081 — Brighter Nepal',               subject='Biology',     format='pdf',   section='College Model Questions',  size_label='5.0 MB',  downloads=3300, tags='["+2","Budhanilkantha","2081"]'),
            Resource(title='B.Sc. CSIT Entrance 2080 Paper & Solutions — Brighter Nepal',             subject='Mathematics', format='pdf',   section='College Model Questions',  size_label='6.3 MB',  downloads=2900, tags='["CSIT","Past Paper","2080"]'),
            # Mathematics Resources
            Resource(title='Integral Calculus Complete Notes — Brighter Nepal (IOE 2081)',             subject='Mathematics', format='pdf',   section='Mathematics',              size_label='14.2 MB', downloads=5100, tags='["Calculus","Integration","IOE"]'),
            Resource(title='Differential Calculus: Limits to Derivatives — Brighter Nepal Notes',     subject='Mathematics', format='pdf',   section='Mathematics',              size_label='12.0 MB', downloads=4600, tags='["Calculus","Differentiation","IOE"]'),
            Resource(title='Coordinate Geometry: Lines, Circles & Conics — Brighter Nepal',           subject='Mathematics', format='pdf',   section='Mathematics',              size_label='10.8 MB', downloads=4200, tags='["Coordinate Geometry","IOE"]'),
            Resource(title='Vectors & 3D Geometry — Brighter Nepal IOE Notes',                        subject='Mathematics', format='pdf',   section='Mathematics',              size_label='8.4 MB',  downloads=3800, tags='["Vectors","3D Geometry","IOE"]'),
            Resource(title='Trigonometry Complete — Brighter Nepal Notes 2081',                       subject='Mathematics', format='pdf',   section='Mathematics',              size_label='9.6 MB',  downloads=4000, tags='["Trigonometry","IOE"]'),
            Resource(title='Permutations, Combinations & Probability — Brighter Nepal',               subject='Mathematics', format='pdf',   section='Mathematics',              size_label='6.2 MB',  downloads=3400, tags='["Probability","IOE","CSIT"]'),
            Resource(title='Matrix & Determinants Quick Reference — Brighter Nepal',                  subject='Mathematics', format='notes', section='Mathematics',              size_label='4.5 MB',  downloads=3100, tags='["Matrix","IOE"]'),
            Resource(title='Integral Calculus Video Lecture — Er. Bikash Pokharel',                   subject='Mathematics', format='video', section='Mathematics',              size_label='1:52:00', downloads=2400, tags='["Calculus","IOE","Lecture"]'),
            Resource(title='Differential Equations Video Lecture — Er. Bikash Pokharel',              subject='Mathematics', format='video', section='Mathematics',              size_label='1:38:00', downloads=2100, tags='["Differential Equations","IOE","Lecture"]'),
            # Physics Resources
            Resource(title='Rotational Dynamics Complete Notes — Brighter Nepal 2081',                subject='Physics',     format='pdf',   section='Physics',                  size_label='11.6 MB', downloads=5400, tags='["Mechanics","Rotation","IOE"]'),
            Resource(title='Electromagnetic Induction & AC Circuits — Brighter Nepal Notes',          subject='Physics',     format='pdf',   section='Physics',                  size_label='9.8 MB',  downloads=4900, tags='["Electromagnetism","IOE"]'),
            Resource(title='Optics: Reflection, Refraction & Diffraction — Brighter Nepal',          subject='Physics',     format='pdf',   section='Physics',                  size_label='10.2 MB', downloads=4600, tags='["Optics","IOE","IOM"]'),
            Resource(title='Thermodynamics & Heat — Brighter Nepal IOE Notes',                       subject='Physics',     format='pdf',   section='Physics',                  size_label='8.8 MB',  downloads=4300, tags='["Thermodynamics","IOE"]'),
            Resource(title='Modern Physics: Photoelectric Effect & Nuclear — Brighter Nepal',        subject='Physics',     format='pdf',   section='Physics',                  size_label='9.0 MB',  downloads=4100, tags='["Modern Physics","IOE","IOM"]'),
            Resource(title='Current Electricity & Circuits — Brighter Nepal Notes 2081',             subject='Physics',     format='pdf',   section='Physics',                  size_label='7.6 MB',  downloads=3900, tags='["Electricity","IOE"]'),
            Resource(title='Measurement & Error Analysis — Brighter Nepal Physics Notes',            subject='Physics',     format='pdf',   section='Physics',                  size_label='5.8 MB',  downloads=4700, tags='["Measurement","IOE","IOM"]'),
            Resource(title='Physics Video: Electromagnetic Induction — Er. Sanjaya Shrestha',       subject='Physics',     format='video', section='Physics',                  size_label='1:45:00', downloads=2300, tags='["Electromagnetism","IOE","Lecture"]'),
            # Chemistry Resources
            Resource(title='Organic Chemistry: Aliphatic & Cyclic Compounds — Brighter Nepal',      subject='Chemistry',   format='pdf',   section='Chemistry',                size_label='13.4 MB', downloads=5000, tags='["Organic Chemistry","IOE","IOM"]'),
            Resource(title='Aromatic Compounds & Named Reactions — Brighter Nepal 2081',             subject='Chemistry',   format='pdf',   section='Chemistry',                size_label='11.0 MB', downloads=4500, tags='["Aromatic Chemistry","IOE","CEE"]'),
            Resource(title='Physical Chemistry: Gaseous State & Thermodynamics — Brighter Nepal',   subject='Chemistry',   format='pdf',   section='Chemistry',                size_label='10.4 MB', downloads=4100, tags='["Physical Chemistry","IOE"]'),
            Resource(title='Electrochemistry & Galvanic Cells — Brighter Nepal Quick Notes',        subject='Chemistry',   format='notes', section='Chemistry',                size_label='4.2 MB',  downloads=3600, tags='["Electrochemistry","IOE","CEE"]'),
            Resource(title='Chemical Kinetics & Equilibrium — Brighter Nepal Notes',                subject='Chemistry',   format='pdf',   section='Chemistry',                size_label='8.6 MB',  downloads=3800, tags='["Kinetics","IOE","CEE"]'),
            Resource(title='Inorganic Chemistry: Transition Metals & Coordination — Brighter Nepal',subject='Chemistry',   format='pdf',   section='Chemistry',                size_label='9.2 MB',  downloads=3200, tags='["Inorganic Chemistry","IOE","IOM"]'),
            Resource(title='Chemistry Practical Guide: Lab Techniques & Safety — Brighter Nepal',   subject='Chemistry',   format='pdf',   section='Chemistry',                size_label='6.4 MB',  downloads=2800, tags='["Practical","Chemistry","IOM"]'),
            # Biology Resources
            Resource(title='Cell Biology & Genetics Complete Notes — Brighter Nepal CEE 2081',      subject='Biology',     format='pdf',   section='Biology',                  size_label='14.8 MB', downloads=5600, tags='["Cell Biology","Genetics","IOM","CEE"]'),
            Resource(title='Human Anatomy & Physiology — Brighter Nepal IOM Notes',                subject='Biology',     format='pdf',   section='Biology',                  size_label='13.2 MB', downloads=5200, tags='["Anatomy","Physiology","IOM","CEE"]'),
            Resource(title='Plant Kingdom: Taxonomy to Physiology — Brighter Nepal Notes',          subject='Biology',     format='pdf',   section='Biology',                  size_label='11.6 MB', downloads=4400, tags='["Botany","IOM","CEE"]'),
            Resource(title='Ecology, Biodiversity & Conservation — Brighter Nepal CEE Notes',       subject='Biology',     format='pdf',   section='Biology',                  size_label='9.8 MB',  downloads=4000, tags='["Ecology","IOM","CEE"]'),
            Resource(title='Microbiology & Immunology Quick Reference — Brighter Nepal',            subject='Biology',     format='notes', section='Biology',                  size_label='5.6 MB',  downloads=3400, tags='["Microbiology","IOM","Nursing"]'),
            Resource(title='Biology Diagram Practice Sheets — CEE 2081 Prep',                      subject='Biology',     format='pdf',   section='Biology',                  size_label='7.8 MB',  downloads=4200, tags='["Diagrams","Biology","CEE"]'),
            Resource(title='Biology Video: Cell Division & Genetics — Dr. Kabita Adhikari',        subject='Biology',     format='video', section='Biology',                  size_label='1:30:00', downloads=2600, tags='["Genetics","IOM","CEE","Lecture"]'),
            # English Resources
            Resource(title='English Grammar Complete Guide — Brighter Nepal IOE/CEE 2081',          subject='English',     format='pdf',   section='English',                  size_label='9.4 MB',  downloads=5800, tags='["Grammar","English","IOE","CEE"]'),
            Resource(title='Reading Comprehension Practice Sets — Brighter Nepal',                  subject='English',     format='pdf',   section='English',                  size_label='6.8 MB',  downloads=4900, tags='["Reading","English","IOE"]'),
            Resource(title='Vocabulary Builder: 3000 Words for Entrance Exams',                    subject='English',     format='notes', section='English',                  size_label='4.8 MB',  downloads=5200, tags='["Vocabulary","English","IOE","CEE"]'),
            Resource(title='Error Detection & Sentence Correction — Brighter Nepal',               subject='English',     format='pdf',   section='English',                  size_label='5.2 MB',  downloads=4300, tags='["Grammar","Error Detection","IOE"]'),
            # Computer / CSIT
            Resource(title='Computer Fundamentals & Architecture — Brighter Nepal CSIT Notes',     subject='Computer',    format='pdf',   section='Extra Study Materials',    size_label='11.2 MB', downloads=3200, tags='["CSIT","Computer","BIT"]'),
            Resource(title='Data Structures & Algorithms Overview — Brighter Nepal CSIT',          subject='Computer',    format='pdf',   section='Extra Study Materials',    size_label='9.6 MB',  downloads=2800, tags='["CSIT","DSA","BIT"]'),
            Resource(title='Digital Logic & Microprocessors — Brighter Nepal CSIT Notes',          subject='Computer',    format='pdf',   section='Extra Study Materials',    size_label='8.4 MB',  downloads=2500, tags='["CSIT","Digital","BIT"]'),
            # Nursing & Paramedical
            Resource(title='Nursing Science Entrance Notes — Brighter Nepal 2081',                 subject='Biology',     format='pdf',   section='Extra Study Materials',    size_label='12.0 MB', downloads=2900, tags='["Nursing","CTEVT","Staff Nurse"]'),
            Resource(title='HA & Lab Technician Entrance Guide — Brighter Nepal',                  subject='Biology',     format='pdf',   section='Extra Study Materials',    size_label='8.8 MB',  downloads=2200, tags='["HA","Lab Technician","CTEVT"]'),
            # Extra Study Materials
            Resource(title='Advanced Maths Worksheet Pack (150 Problems) — Brighter Nepal',        subject='Mathematics', format='pdf',   section='Extra Study Materials',    size_label='3.8 MB',  downloads=4100, tags='["Worksheet","Mathematics","IOE","Extra"]'),
            Resource(title='Physics Formula Sheet — All Chapters — Brighter Nepal 2081',           subject='Physics',     format='notes', section='Extra Study Materials',    size_label='2.6 MB',  downloads=5500, tags='["Formula","Physics","IOE","Quick Reference"]'),
            Resource(title='Chemistry Reaction Chart — Organic & Inorganic — Brighter Nepal',      subject='Chemistry',   format='notes', section='Extra Study Materials',    size_label='2.2 MB',  downloads=4800, tags='["Reactions","Chemistry","Quick Reference"]'),
            Resource(title='Biology Mind Maps — All Systems — Brighter Nepal CEE Prep',            subject='Biology',     format='pdf',   section='Extra Study Materials',    size_label='6.0 MB',  downloads=4200, tags='["Mind Maps","Biology","CEE","IOM"]'),
            Resource(title='GK & Current Affairs for Entrance Exams — Brighter Nepal',             subject='English',     format='pdf',   section='Extra Study Materials',    size_label='5.4 MB',  downloads=3800, tags='["GK","Current Affairs","IOE","CEE"]'),
            Resource(title='Time Management & Exam Strategy Guide — Brighter Nepal',               subject='English',     format='notes', section='Extra Study Materials',    size_label='1.8 MB',  downloads=3200, tags='["Strategy","Exam Tips","IOE","CEE"]'),
        ]
        db.session.add_all(resources)

        # ── Notices ───────────────────────────────────────────────────────────
        notices_data = [
            (
                'IOE Entrance Exam 2081 Date Officially Announced — Must Read',
                'Tribhuvan University\'s Institute of Engineering has officially announced the IOE Entrance Examination 2081 date. All Brighter Nepal IOE Batch students must submit their registration forms before the deadline. Late registration will not be accepted. Visit the TU-IOE official site for updates or contact our admin desk immediately.',
                'urgent', 'Academic Affairs', 'https://ioe.tu.edu.np', True, now - timedelta(hours=6),
            ),
            (
                'CEE 2081 Registration Deadline — Chaitra 20',
                'The last date to register for the CEE 2081 (IOM MBBS/BDS Entrance) is Chaitra 20, 2081. Brighter Nepal admin office is assisting students with form filling and document submission. Visit our front desk between 8 AM – 5 PM.',
                'urgent', 'Academic Affairs', 'https://ctevt.org.np', True, now - timedelta(days=1),
            ),
            (
                'Free Trial Access Ends Chaitra 30 — Upgrade Now',
                'Attention trial students! Your 7-day free trial expires on Chaitra 30. After expiry, access to live classes, model sets, and study materials will be restricted. Upgrade your plan today to continue seamless preparation without interruption.',
                'important', 'Admin Office', '#', True, now - timedelta(days=2),
            ),
            (
                'Grand Full IOE Simulation Exam — Falgun 25 (Compulsory)',
                'A compulsory Grand IOE Simulation Exam (3 hours, 100 marks) will be held on Falgun 25, 2081, at Brighter Nepal Main Exam Hall starting at 7:00 AM sharp. Bring your admit card and stationery. No entry after 7:15 AM.',
                'important', 'Examination Cell', '#', False, now - timedelta(days=3),
            ),
            (
                'CEE Grand Medical Mock Exam — Falgun 27 (Compulsory)',
                'Compulsory Grand CEE Medical Mock Exam (3 hours, 200 marks) for all IOM/CEE batch students on Falgun 27, 2081. Venue: Brighter Nepal Exam Hall, Batch A 6:30 AM, Batch B 11:00 AM.',
                'important', 'Examination Cell', '#', False, now - timedelta(days=3),
            ),
            (
                'Scholarship Test Results Published — Brighter Nepal 2081',
                'Results of the Brighter Nepal Scholarship Test are now published. Top 15 students receive fee waivers ranging from 25% to 100%. Check your result at the admin desk or on your registered email. Scholarships will be credited within 5 working days.',
                'general', 'Academic Affairs', '#', False, now - timedelta(days=5),
            ),
            (
                'New Study Materials Added — IOE 2080 & 2079 Complete Solutions',
                'Complete solved question papers for IOE Entrance 2080 and 2079 have been uploaded in the Study Materials section. All IOE Batch students are encouraged to download and practice these papers at the earliest.',
                'general', 'Content Team', '#', False, now - timedelta(days=6),
            ),
            (
                'Physics Lab Practical Session Schedule — IOM Batch',
                'Updated Physics Practical session schedule for IOM/CEE batch has been uploaded. Students must confirm their lab slot at the Science Lab desk (Ground Floor). Report in proper lab attire. First session starts Falgun 22.',
                'general', 'Science Department', '#', False, now - timedelta(days=8),
            ),
            (
                'Brighter Nepal Annual Merit Felicitation Ceremony — Chaitra 5',
                'Brighter Nepal\'s Annual Merit Felicitation Ceremony honoring top-performing students will be held on Chaitra 5, 2081, at our Main Campus auditorium. All students and parents are cordially invited. Program starts at 11:00 AM.',
                'general', 'Admin Office', '#', False, now - timedelta(days=10),
            ),
            (
                'Parent-Teacher Meeting — Scheduled for Falgun 28',
                'A Parent-Teacher Meeting (PTM) is scheduled for Falgun 28, 2081, from 10 AM to 2 PM. All guardians are requested to attend and review their ward\'s performance with respective subject teachers. Attendance is compulsory for parents of trial-plan students.',
                'general', 'Admin Office', '#', False, now - timedelta(days=12),
            ),
            (
                'IOE/CEE Toppers\' Strategy Session — Open to All Batches',
                'Brighter Nepal is hosting a special "Toppers\' Strategy Session" featuring previous IOE Pulchowk and CEE MBBS toppers on Falgun 30. Limited seats — first come, first served. Register at admin desk by Falgun 28.',
                'important', 'Academic Affairs', '#', False, now - timedelta(days=14),
            ),
            (
                'New Batch Starting: +2 Science & Management Bridge Course',
                'Registration is now open for the New +2 Science and Management Bridge Course batch (Post-SEE 2081). Classes commence from Baisakh 1, 2082. Early-bird discount of 15% available until Chaitra 25. Contact admin for details.',
                'general', 'Admissions', '#', False, now - timedelta(days=16),
            ),
        ]
        for n_data in notices_data:
            n = Notice(
                title=n_data[0], body=n_data[1], category=n_data[2],
                department=n_data[3], link_url=n_data[4],
                is_pinned=n_data[5], created_at=n_data[6],
            )
            db.session.add(n)

        # ── Payments ──────────────────────────────────────────────────────────
        db.session.flush()
        payment_methods   = ['eSewa', 'Khalti', 'Bank Transfer', 'IME Pay', 'fonePay', 'eSewa', 'Khalti']
        payment_statuses  = ['completed', 'completed', 'completed', 'completed', 'pending', 'failed', 'completed']
        # Different fee tiers per batch type
        def fee_for_group(gid):
            if gid == groups[0].id: return 9500.0   # IOE
            if gid == groups[1].id: return 10500.0  # IOM/CEE
            if gid == groups[2].id: return 7500.0   # CSIT
            if gid == groups[3].id: return 6500.0   # +2 Science
            if gid == groups[4].id: return 5500.0   # +2 Management
            return 5000.0                            # Nursing/Paramedical

        for i, student in enumerate(student_objs):
            amount = fee_for_group(student.group_id)
            p = Payment(
                user_id=student.id,
                amount=amount,
                method=payment_methods[i % len(payment_methods)],
                status=payment_statuses[i % len(payment_statuses)],
                created_at=now - timedelta(days=i * 4),
            )
            db.session.add(p)

        # ── Group Messages ────────────────────────────────────────────────────
        db.session.flush()
        group_messages = [
            # IOE group
            GroupMessage(group_id=groups[0].id, user_id=admin.id,              created_at=now - timedelta(hours=8),
                text="🎓 Good morning, Brighter Nepal IOE Batch 2081! IOE Mock Sets A, B & C are now LIVE in Study Materials. Attempt all three before the Grand Simulation Exam on Falgun 25. Best of luck! 💪"),
            GroupMessage(group_id=groups[0].id, user_id=coordinator.id,        created_at=now - timedelta(hours=4),
                text="📢 Reminder: Tonight's LIVE class on Definite Integration by Er. Bikash Pokharel sir starts at 7:00 PM. It will cover IOE past questions from 2075–2081. Don't miss it! 🔥"),
            GroupMessage(group_id=groups[0].id, user_id=faculty_objs[0].id,    created_at=now - timedelta(hours=1),
                text="Hi IOE Batch! I've uploaded a brand-new Integration Worksheet (150 problems) to the Study Materials. Print it out or solve it digitally. Bring your doubts to tomorrow's QAD session. — Er. Bikash Pokharel"),
            # IOM / CEE group
            GroupMessage(group_id=groups[1].id, user_id=admin.id,              created_at=now - timedelta(hours=7),
                text="🧬 Brighter Nepal IOM/CEE Batch! CEE Medical Mock Sets A, B & C are now available. The Grand Medical Mock Exam is on Falgun 27 — make sure you practice ALL three sets before then! 🏥"),
            GroupMessage(group_id=groups[1].id, user_id=faculty_objs[2].id,    created_at=now - timedelta(hours=3),
                text="CEE students — I've updated the Human Physiology notes with additional diagrams. Download the latest version from Study Materials > Biology. Focus especially on the cardiorespiratory diagrams for CEE. — Dr. Kabita Adhikari"),
            GroupMessage(group_id=groups[1].id, user_id=coordinator.id,        created_at=now - timedelta(hours=2),
                text="📝 CEE 2081 Registration deadline is Chaitra 20. Visit the admin desk by Chaitra 18 to complete your paperwork. We'll help you with the forms. Don't leave it for the last minute!"),
            # CSIT group
            GroupMessage(group_id=groups[2].id, user_id=admin.id,              created_at=now - timedelta(hours=6),
                text="💻 Brighter Nepal CSIT Batch! New CSIT Mock Sets A & B are live. Also, Er. Nabin sir's CSIT Data Structures lecture recording is now uploaded. Stream it anytime — Study Materials > Computer. 🚀"),
            GroupMessage(group_id=groups[2].id, user_id=faculty_objs[5].id,    created_at=now - timedelta(hours=2),
                text="CSIT students — for binary number conversion problems: practice at least 20 conversions per day. It's a guaranteed question in every CSIT entrance. Worksheet coming tomorrow! — Er. Nabin Acharya"),
            # +2 Science Bridge Course group
            GroupMessage(group_id=groups[3].id, user_id=admin.id,              created_at=now - timedelta(hours=5),
                text="🌟 +2 Science Bridge Course students! The St. Xavier's and Budhanilkantha Entrance Mock papers are now available in Study Materials > College Model Questions. Practice them seriously — only a few weeks left! 🏫"),
            GroupMessage(group_id=groups[3].id, user_id=faculty_objs[4].id,    created_at=now - timedelta(hours=3),
                text="English students — remember: St. Xavier's entrance carries 25 marks of English. Focus on vocabulary and comprehension passages from our Vocabulary Builder (3000 Words) notes. — Ms. Sunita Thapa"),
            # +2 Management group
            GroupMessage(group_id=groups[4].id, user_id=admin.id,              created_at=now - timedelta(hours=5),
                text="📊 Management Batch! Your weekly test on Accountancy basics is scheduled for Baisakh 3. Make sure you've completed Chapters 1–5 of the Management notes. Ask your class representative for the study schedule."),
            # Staff Nurse / Paramedical group
            GroupMessage(group_id=groups[5].id, user_id=admin.id,              created_at=now - timedelta(hours=4),
                text="🏥 Nursing & Paramedical Batch! The Nursing Science Entrance Notes and HA/Lab Technician Entrance Guide have been updated. Download them from Extra Study Materials. Good luck with your preparation! 💉"),
            GroupMessage(group_id=groups[5].id, user_id=coordinator.id,        created_at=now - timedelta(hours=1),
                text="Reminder: Microbiology & Immunology section carries about 20% marks in the Staff Nurse entrance. Do NOT skip it! The Quick Reference notes are in Study Materials > Biology. — Roshan Paudel"),
        ]
        db.session.add_all(group_messages)

        db.session.commit()

        print(
            f"\n✅  Brighter Nepal Bridgecourse seed complete:\n"
            f"   👥  {len(groups)} groups\n"
            f"   👤  {2 + len(faculty_data) + len(student_objs)} users "
            f"(1 super-admin + 1 coordinator + {len(faculty_data)} faculty + {len(student_objs)} students)\n"
            f"   📚  {len(model_sets)} model sets\n"
            f"   📝  {len(tests)} weekly tests "
            f"({sum(1 for t in tests if t.status=='live')} live, "
            f"{sum(1 for t in tests if t.status=='scheduled')} scheduled, "
            f"{sum(1 for t in tests if t.status=='completed')} completed)\n"
            f"   📡  {len(classes)} live classes\n"
            f"   📄  {len(resources)} resources\n"
            f"   📢  {len(notices_data)} notices\n"
            f"   💳  {len(student_objs)} payments\n"
            f"   💬  {len(group_messages)} group messages\n"
            f"\n🔐  Admin :       admin@brighternepal.edu.np  /  BrighterAdmin@2081\n"
            f"🔐  Coordinator:  coordinator@brighternepal.edu.np  /  BrighterAdmin@2081\n"
            f"🔐  Student:      aashish.maharjan@gmail.com  /  Student@2081"
        )


if __name__ == '__main__':
    seed()