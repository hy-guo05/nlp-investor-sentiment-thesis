# -*- coding: utf-8 -*-
"""Push all repo files to GitHub via the REST API (api.github.com).
Works when github.com:443 git protocol is blocked but the API is reachable.
Usage: python push_via_api.py <token>"""
import base64, json, os, sys, urllib.request, urllib.error

TOKEN = sys.argv[1]
OWNER = "hy-guo05"
REPO = "nlp-investor-sentiment-thesis"
BRANCH = "main"
API = "https://api.github.com"
ROOT = os.path.dirname(os.path.abspath(__file__))

# 需要上传的文件（相对路径）；跳过 .git 等
SKIP_DIRS = {".git", "__pycache__", "site", "venv", ".venv"}
SKIP_EXT = {".pyc"}


def api(method, path, payload=None):
    url = API + path
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "token " + TOKEN)
    req.add_header("User-Agent", "thesis-push")
    req.add_header("Accept", "application/vnd.github+json")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        return e.code, body


def collect():
    files = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if os.path.splitext(fn)[1] in SKIP_EXT:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, ROOT).replace("\\", "/")
            files.append((rel, full))
    return sorted(files)


def main():
    files = collect()
    print("files to upload:", len(files))
    for rel, _ in files:
        print("   ", rel)

    for rel, full in files:
        with open(full, "rb") as f:
            content = base64.b64encode(f.read()).decode("ascii")

        # check if exists (to get sha for update)
        st, existing = api("GET", f"/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(rel)}?ref={BRANCH}")
        sha = existing.get("sha") if st == 200 and isinstance(existing, dict) else None

        payload = {"message": f"Add {rel}", "content": content, "branch": BRANCH}
        if sha:
            payload["sha"] = sha
            payload["message"] = f"Update {rel}"

        st, res = api("PUT", f"/repos/{OWNER}/{REPO}/contents/{urllib.parse.quote(rel)}", payload)
        if st in (200, 201):
            print(f"[OK {st}] {rel}")
        else:
            print(f"[FAIL {st}] {rel} -> {res}")


if __name__ == "__main__":
    main()
