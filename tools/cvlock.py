#!/usr/bin/env python3
"""Encrypt the CV bank for the test page.
Reads the plain CV records from index.html (cvdata) and the images cv/{id}.jpg,
and writes test/cvx/: keys.json (data key wrapped per PIN), data.bin, {id}.bin.
Usage: CV_PIN=xxxx python3 -I tools/cvlock.py <repo dir>
       optional CV_ADD_PIN=yyyy adds another PIN (same data key)."""
import base64, hashlib, json, os, re, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 600000
root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
out = os.path.join(root, "test", "cvx")
os.makedirs(out, exist_ok=True)
b64 = lambda b: base64.b64encode(b).decode()
ub64 = base64.b64decode

def kek(pin, salt, it):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=it).derive(pin.encode())

def enc(key, data):
    iv = os.urandom(12)
    return iv + AESGCM(key).encrypt(iv, data, None)

def dec(key, blob):
    return AESGCM(key).decrypt(blob[:12], blob[12:], None)

def wrap(pin, dk):
    s = os.urandom(16); iv = os.urandom(12)
    return {"s": b64(s), "iv": b64(iv), "w": b64(AESGCM(kek(pin, s, ITER)).encrypt(iv, dk, None))}

pin = os.environ.get("CV_PIN", "")
if not pin:
    sys.exit("CV_PIN is required")
kp = os.path.join(out, "keys.json")
if os.path.exists(kp):
    meta = json.load(open(kp))
    dk = None
    for k in meta["keys"]:
        try:
            dk = AESGCM(kek(pin, ub64(k["s"]), meta["it"])).decrypt(ub64(k["iv"]), ub64(k["w"]), None); break
        except Exception:
            pass
    if dk is None:
        sys.exit("CV_PIN does not match any key in keys.json")
else:
    dk = AESGCM.generate_key(256)
    meta = {"v": 1, "it": ITER, "keys": [wrap(pin, dk)]}
if os.environ.get("CV_ADD_PIN"):
    meta["keys"].append(wrap(os.environ["CV_ADD_PIN"], dk))

html = open(os.path.join(root, "index.html"), encoding="utf-8").read()
m = re.search(r'<script type="application/json" id="cvdata">(.*?)</script>', html, re.S)
recs = json.loads(m.group(1))

old = {}
dp = os.path.join(out, "data.bin")
if os.path.exists(dp):
    try:
        old = {r["id"]: r.get("_h") for r in json.loads(dec(dk, open(dp, "rb").read()))}
    except Exception:
        old = {}

ids = set()
for r in recs:
    ids.add(r["id"])
    if r.get("img"):
        jp = os.path.join(root, "cv", f'{r["id"]}.jpg')
        raw = open(jp, "rb").read()
        h = hashlib.sha256(raw).hexdigest()[:16]
        bp = os.path.join(out, f'{r["id"]}.bin')
        if old.get(r["id"]) != h or not os.path.exists(bp):
            open(bp, "wb").write(enc(dk, raw))
        r["_h"] = h
        r["img"] = f'cvx/{r["id"]}.bin'
for f in os.listdir(out):
    if f.endswith(".bin") and f != "data.bin" and int(f[:-4]) not in ids:
        os.remove(os.path.join(out, f))
open(dp, "wb").write(enc(dk, json.dumps(recs, ensure_ascii=False, separators=(",", ":")).encode()))
meta["n"] = len(recs)
json.dump(meta, open(kp, "w"), separators=(",", ":"))
print(f"encrypted {len(recs)} records, {len(meta['keys'])} key(s)")
