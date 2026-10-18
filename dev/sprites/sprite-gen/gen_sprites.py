#!/usr/bin/env python3
"""Generate the rider sprite sheets with the OpenAI Images API (edits endpoint, with reference images).

Usage:
  python gen_sprites.py list                 # show the sheets
  python gen_sprites.py charref              # step 1: pixel-art character model sheet (from refs/ only)
  python gen_sprites.py sheet1               # step 2: sheet 1 (refs/ + approved/charref.png)
  python gen_sprites.py all                  # step 3: every other sheet (refs/ + approved/charref.png + approved/sheet1.png)
Options:
  --n 2              number of variants per sheet (default 2)
  --quality high     low | medium | high (default high)
  --model gpt-image-2
  --dry-run          print what would be sent, call nothing

Needs: Python 3.9+, `pip install requests`, and the OPENAI_API_KEY environment variable.
"""
import argparse, base64, json, os, sys, time
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency: run  pip install requests")

ROOT = Path(__file__).resolve().parent
REFS, APPROVED, OUT = ROOT / "refs", ROOT / "approved", ROOT / "output"
API = "https://api.openai.com/v1/images/edits"
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp"}
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def load_sheets():
    return json.loads((ROOT / "sheets.json").read_text(encoding="utf-8"))


def reference_files(sheet):
    files = sorted(p for p in REFS.glob("*") if p.suffix.lower() in IMG_EXT)
    if not files:
        sys.exit(f"No reference image in {REFS}. Put your character photos there (png, jpg or webp).")
    for dep in sheet.get("uses", []):
        p = next((APPROVED / f"{dep}{e}" for e in (".png", ".jpg", ".jpeg", ".webp") if (APPROVED / f"{dep}{e}").exists()), None)
        if not p:
            sys.exit(f"{sheet['id']} needs your approved {dep}: copy the variant you chose to {APPROVED / (dep + '.png')}")
        files.append(p)
    return files


def call_api(key, model, sheet, files, n, quality, fidelity):
    data = {"model": model, "prompt": sheet["prompt"], "size": sheet["size"], "quality": quality, "n": str(n), "output_format": "png"}
    if fidelity:
        data["input_fidelity"] = "high"   # keeps the faces closer to the references, when the model supports it
    handles = [open(p, "rb") for p in files]
    try:
        up = [("image[]", (p.name, h, MIME[p.suffix.lower()])) for p, h in zip(files, handles)]
        return requests.post(API, headers={"Authorization": f"Bearer {key}"}, data=data, files=up, timeout=600)
    finally:
        for h in handles:
            h.close()


def generate(sheet, args, key):
    files = reference_files(sheet)
    print(f"\n== {sheet['id']}: {sheet['name']}  ({sheet['size']}, {args.n} variant(s), {args.quality})")
    print("   references: " + ", ".join(p.name for p in files))
    if args.dry_run:
        print("   (dry run, nothing sent)")
        return
    fidelity = True
    for attempt in range(1, 4):
        t0 = time.time()
        try:
            r = call_api(key, args.model, sheet, files, args.n, args.quality, fidelity)
        except requests.RequestException as e:
            if attempt < 3:
                print(f"   network error ({e.__class__.__name__}), retrying in {10 * attempt} s"); time.sleep(10 * attempt); continue
            print(f"   FAILED, network error: {e}"); return
        if r.status_code == 200:
            break
        body = r.text[:800]
        if r.status_code == 400 and "input_fidelity" in body and fidelity:
            print("   the model refuses input_fidelity, retrying without it")
            fidelity = False
            continue
        if r.status_code in (429, 500, 502, 503, 504) and attempt < 3:
            print(f"   HTTP {r.status_code}, retrying in {10 * attempt} s")
            time.sleep(10 * attempt)
            continue
        print(f"   FAILED, HTTP {r.status_code}:\n   {body}")
        return
    else:
        print("   FAILED after retries")
        return
    OUT.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, item in enumerate(r.json().get("data", []), 1):
        path = OUT / f"{sheet['id']}_{stamp}_v{i}.png"
        path.write_bytes(base64.b64decode(item["b64_json"]))
        print(f"   saved {path.relative_to(ROOT)}")
    print(f"   done in {time.time() - t0:.0f} s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--n", type=int, default=2)
    ap.add_argument("--quality", default="high", choices=["low", "medium", "high"])
    ap.add_argument("--model", default=os.environ.get("IMAGE_MODEL", "gpt-image-2"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    sheets = load_sheets()
    by_id = {s["id"]: s for s in sheets}
    if args.targets == ["list"]:
        for s in sheets:
            print(f"{s['id']:8} {s['size']:10} {'refs + ' + ' + '.join(s['uses']) if s['uses'] else 'refs only':24} {s['name']}")
        return
    ids = [s["id"] for s in sheets if s["id"] not in ("charref", "sheet1")] if args.targets == ["all"] else args.targets
    unknown = [i for i in ids if i not in by_id]
    if unknown:
        sys.exit(f"Unknown sheet(s): {', '.join(unknown)}. Run: python gen_sprites.py list")
    key = os.environ.get("OPENAI_API_KEY")
    if not key and not args.dry_run:
        sys.exit("Set the OPENAI_API_KEY environment variable first.")
    for i in ids:
        generate(by_id[i], args, key)


if __name__ == "__main__":
    main()
