import urllib.parse
import json
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def cache_key_with_user():
    """
    Generates a cache key that includes the current user's ID
    to ensure user-specific data is not leaked to other users.
    Falls back to 'anon' for unauthenticated requests.
    """
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        user_id = 'anon'
        if identity:
            if isinstance(identity, dict):
                user_id = str(identity.get('id', 'anon'))
            else:
                user_id = str(json.loads(identity).get('id', 'anon'))
    except Exception:
        user_id = 'anon'
        
    qs = urllib.parse.urlencode(request.args)
    return f"{request.path}?{qs}&u={user_id}"
