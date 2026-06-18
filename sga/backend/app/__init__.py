# app package

# Monkeypatch bcrypt.hashpw to avoid passlib crash on modern bcrypt versions (> 4.0.0)
try:
    import bcrypt
    original_hashpw = bcrypt.hashpw
    def patched_hashpw(password, salt):
        if isinstance(password, bytes) and len(password) > 72:
            password = password[:72]
        elif isinstance(password, str) and len(password.encode('utf-8')) > 72:
            password = password.encode('utf-8')[:72]
        return original_hashpw(password, salt)
    bcrypt.hashpw = patched_hashpw
except Exception:
    pass
