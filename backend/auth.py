"""Minimal login, standard library only. Users come from the AUTH_USERS env var ("alice:pw1,bob:pw2"), kept PBKDF2-hashed in memory.
Sessions are HMAC-signed expiring bearer tokens (set AUTH_SECRET so they survive a restart). No database: this gates access, it is not a user system."""
import base64, hashlib, hmac, json, os, secrets, time
from fastapi import Header, HTTPException

TTL = 12 * 3600
SECRET = (os.getenv("AUTH_SECRET") or secrets.token_hex(32)).encode()
SALT = secrets.token_bytes(16)
hash_pw = lambda pw: hashlib.pbkdf2_hmac("sha256", pw.encode(), SALT, 100_000)

_cfg = os.getenv("AUTH_USERS") or "demo:epc-demo"
USERS = {u.strip(): hash_pw(p) for u, _, p in (x.partition(":") for x in _cfg.split(",")) if u.strip() and p}
if not os.getenv("AUTH_USERS"): print("WARNING: AUTH_USERS not set, using the built-in demo account. Set AUTH_USERS before deploying.")
FAILS: dict = {}                                   # username -> timestamps of recent failed logins

b64 = lambda b: base64.urlsafe_b64encode(b).decode().rstrip("=")
sign = lambda body: b64(hmac.new(SECRET, body.encode(), hashlib.sha256).digest())

def login(username: str, password: str) -> dict:
    now = time.time(); recent = [t for t in FAILS.get(username, []) if now - t < 60]
    if len(recent) >= 5: raise HTTPException(429, "Too many failed attempts. Wait a minute and try again.")
    ok = hmac.compare_digest(USERS.get(username, b""), hash_pw(password)) and username in USERS
    if not ok:
        if len(FAILS) > 1000: FAILS.clear()
        FAILS[username] = recent + [now]; raise HTTPException(401, "Incorrect username or password.")
    FAILS.pop(username, None)
    body = b64(json.dumps({"u": username, "exp": int(now) + TTL}).encode())
    return {"token": f"{body}.{sign(body)}", "user": username, "expires_in": TTL}

def current_user(authorization: str = Header(default="")) -> str:
    """FastAPI dependency: returns the username or raises 401."""
    try:
        body, sig = authorization.removeprefix("Bearer ").split(".")
        p = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
        if hmac.compare_digest(sig, sign(body)) and p["exp"] > time.time() and p["u"] in USERS: return p["u"]
    except Exception: pass
    raise HTTPException(401, "Not authenticated")
