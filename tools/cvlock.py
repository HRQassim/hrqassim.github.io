#!/usr/bin/env python3
"""Encrypted CV bank store (cvx/ at the repo root, used by index.html and test/index.html).
The records and CV images are AES-GCM encrypted with one data key; keys.json holds that key
wrapped once per access PIN (PBKDF2-SHA256). Every command needs CV_PIN in the environment.

  python3 -I tools/cvlock.py dump  <out.json>        decrypt records to a plain JSON file (keep it OUTSIDE the repo)
  python3 -I tools/cvlock.py save  <in.json>         encrypt records from a JSON file into cvx/data.bin
  python3 -I tools/cvlock.py img   <id> <file.jpg>   encrypt a CV image into cvx/<id>.bin
  python3 -I tools/cvlock.py getimg <id> <out.jpg>   decrypt a CV image
  python3 -I tools/cvlock.py rm    <id>              delete cvx/<id>.bin
  python3 -I tools/cvlock.py addpin                  add CV_ADD_PIN as another PIN (same data)
Run from the repo root."""
import base64, json, os, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ITER = 600000
OUT = os.path.abspath("cvx")
b64 = lambda b: base64.b64encode(b).decode()
ub64 = base64.b64decode
kek = lambda pin, salt, it: PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=it).derive(pin.encode())
def enc(key, data):
    iv = os.urandom(12); return iv + AESGCM(key).encrypt(iv, data, None)
dec = lambda key, blob: AESGCM(key).decrypt(blob[:12], blob[12:], None)
def wrap(pin, dk):
    s = os.urandom(16); iv = os.urandom(12)
    return {"s": b64(s), "iv": b64(iv), "w": b64(AESGCM(kek(pin, s, ITER)).encrypt(iv, dk, None))}

pin = os.environ.get("CV_PIN") or sys.exit("CV_PIN is required")
os.makedirs(OUT, exist_ok=True)
kp = os.path.join(OUT, "keys.json")
if os.path.exists(kp):
    meta = json.load(open(kp)); dk = None
    for k in meta["keys"]:
        try: dk = AESGCM(kek(pin, ub64(k["s"]), meta["it"])).decrypt(ub64(k["iv"]), ub64(k["w"]), None); break
        except Exception: pass
    if dk is None: sys.exit("CV_PIN does not match any key in keys.json")
else:
    dk = AESGCM.generate_key(256); meta = {"v": 1, "it": ITER, "keys": [wrap(pin, dk)], "n": 0}
save_meta = lambda: json.dump(meta, open(kp, "w"), separators=(",", ":"))
cmd, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
dp = os.path.join(OUT, "data.bin")
if cmd == "dump":
    recs = json.loads(dec(dk, open(dp, "rb").read())) if os.path.exists(dp) else []
    json.dump(recs, open(args[0], "w", encoding="utf-8"), ensure_ascii=False, indent=1); print(len(recs), "records")
elif cmd == "save":
    recs = json.load(open(args[0], encoding="utf-8"))
    for r in recs:
        r.pop("_h", None)
        if r.get("img"): r["img"] = f'cvx/{r["id"]}.bin'
    missing = [r["id"] for r in recs if r.get("img") and not os.path.exists(os.path.join(OUT, f'{r["id"]}.bin'))]
    if missing: sys.exit(f"missing encrypted images for ids {missing}: run img first")
    open(dp, "wb").write(enc(dk, json.dumps(recs, ensure_ascii=False, separators=(",", ":")).encode()))
    meta["n"] = len(recs); save_meta(); print("saved", len(recs), "records")
elif cmd == "img":
    open(os.path.join(OUT, f"{int(args[0])}.bin"), "wb").write(enc(dk, open(args[1], "rb").read())); print("ok")
elif cmd == "getimg":
    open(args[1], "wb").write(dec(dk, open(os.path.join(OUT, f"{int(args[0])}.bin"), "rb").read())); print("ok")
elif cmd == "rm":
    p = os.path.join(OUT, f"{int(args[0])}.bin")
    if os.path.exists(p): os.remove(p)
    print("ok")
elif cmd == "addpin":
    meta["keys"].append(wrap(os.environ.get("CV_ADD_PIN") or sys.exit("CV_ADD_PIN is required"), dk)); save_meta(); print(len(meta["keys"]), "pins")
else:
    sys.exit(__doc__)
