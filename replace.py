path = '/home/bishal-regmi/Desktop/Company Works/BrighterNepal/brighter-nepal-api/app/routes/users.py'
with open(path) as f:
    content = f.read()
import re
old_block = re.search(r"@users_bp\.post\('/bulk'\)\n@admin_required\ndef bulk_create\(\).*?return ok\(\{'created': len\(created_ids\).*?\}, 'Bulk accounts created', 201\)", content, re.DOTALL)
if old_block:
    new_block = """@users_bp.post('/bulk')
@admin_required
def bulk_create():
    data       = request.get_json(silent=True) or {}
    users_data = data.get('users', [])
    created    = []
    for u in users_data:
        name = (u.get('name') or '').strip()
        if not name:
            continue
        raw_email = (u.get('email') or '').strip().lower()
        pw        = u.get('password') or 'Brighter@123'
        
        if raw_email and User.query.filter_by(email=raw_email).first():
            continue
            
        placeholder = f'pending_{id(u)}@placeholder.local'
        user = User(name=name, email=raw_email or placeholder)
        user.set_password(pw)
        user.plan     = u.get('plan', 'trial')
        user.whatsapp = u.get('whatsapp')
        db.session.add(user)
        db.session.flush()
        
        if not raw_email:
            user.email = f'bc{str(user.id).zfill(4)}@brighternepal.local'
        db.session.flush()
        
        created.append({
            'id':       user.id,
            'bc_id':    f'BC-{str(user.id).zfill(4)}',
            'name':     user.name,
            'email':    user.email,
            'password': pw,
            'plan':     user.plan,
        })
    db.session.commit()
    return ok({'created': len(created), 'users': created}, 'Bulk accounts created', 201)"""
    content = content[:old_block.start()] + new_block + content[old_block.end():]
    with open(path, 'w') as f:
        f.write(content)
    print('OK - replaced bulk_create')
else:
    print('NOT FOUND')
