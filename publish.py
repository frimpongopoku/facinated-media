"""Send a rendered week to Buffer: TikTok photo posts and Instagram carousels.

Buffer only takes public image URLs, so the slides are first pushed to this
public GitHub repo (facinated-media) and served from raw.githubusercontent.com.

    python3 publish.py check                     # verify the key, list channels
    python3 publish.py upload weeks/2026-11-02   # commit and push the week (slides, plan, review page)
    python3 publish.py dry-run weeks/2026-11-02  # show what would be sent
    python3 publish.py schedule weeks/2026-11-02 # create the scheduled posts
    python3 publish.py draft weeks/2026-11-02    # create them as Buffer drafts

Created post IDs go to weeks/<week>/buffer.json, so re-running never posts twice.
"""
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).parent
RAW_BASE = "https://raw.githubusercontent.com/frimpongopoku/facinated-media"
API = "https://api.buffer.com"
GHANA_UTC_OFFSET = "Z"  # Ghana is on GMT all year


def env(name):
    """Read a setting from the environment or .env; None when absent."""
    if os.environ.get(name):
        return os.environ[name]
    dotenv = ROOT / ".env"
    for line in (dotenv.read_text().splitlines() if dotenv.exists() else []):
        key, _, value = line.partition("=")
        if key.strip() == name and value.strip() not in ("", "paste-your-key-here"):
            return value.strip()
    return None


def gql(query, variables=None):
    # In the cloud run the key is a network secret: the proxy adds the
    # Authorization header for api.buffer.com, so no key is visible here.
    headers = {"Content-Type": "application/json", "User-Agent": "facinated-content-engine"}
    key = env("BUFFER_API_KEY")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    body = json.dumps({"query": query, "variables": variables or {}}).encode()
    req = urllib.request.Request(API, body, headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"Buffer API error {e.code}: {e.read().decode()[:500]}")
    if data.get("errors"):
        sys.exit(f"Buffer API error: {json.dumps(data['errors'])[:800]}")
    return data["data"]


def channels():
    orgs = gql("query { account { organizations { id name } } }")["account"]["organizations"]
    found = {}
    for org in orgs:
        q = """query($org: OrganizationId!) { channels(input: {organizationId: $org}) {
                 id name service type timezone isDisconnected isLocked isQueuePaused } }"""
        for ch in gql(q, {"org": org["id"]})["channels"]:
            found.setdefault(ch["service"], ch)
    return found


def check():
    chans = channels()
    for service, ch in chans.items():
        flags = [f for f in ("isDisconnected", "isLocked", "isQueuePaused") if ch[f]]
        print(f"{service:10} @{ch['name']:24} {ch['type']:10} tz={ch['timezone']} {' '.join(flags) or 'ready'}")
    missing = {"instagram", "tiktok"} - chans.keys()
    if missing:
        print("Not connected in Buffer:", ", ".join(sorted(missing)))
    return chans


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=True).stdout.strip()


def branch():
    return git("rev-parse", "--abbrev-ref", "HEAD")


def upload(week):
    git("add", week, "docs", "catalog.json")
    if subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--quiet"]).returncode == 0:
        print("repo already up to date")
    else:
        git("commit", "-m", f"Add posts for week {pathlib.Path(week).name}\n\n"
            "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
    git("push", "-u", "origin", branch())
    print(f"pushed {week} to {branch()}")


def image_urls(week, post, platform):
    files = sorted((ROOT / week / post["id"] / platform).glob("*.jpg"))
    base = f"{RAW_BASE}/{branch()}"
    return [f"{base}/{week}/{post['id']}/{platform}/{f.name}" for f in files]


def url_ok(url):
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200 and r.headers.get("Content-Type", "").startswith("image/")
    except urllib.error.URLError:
        return False


def post_inputs(week, post, chans, draft):
    due = f"{post['date']}T{post['time']}:00.000{GHANA_UTC_OFFSET}"
    title = next(s["headline"] for s in post["slides"] if s["type"] == "cover").replace(" ", " ")
    base = {"schedulingType": "automatic", "mode": "customScheduled", "dueAt": due, "aiAssisted": True}
    if draft:
        base["saveToDraft"] = True
    return {
        # Buffer can't attach a TikTok sound, so TikTok posts are sent as phone
        # notifications: Stella opens them in the TikTok app and adds a sound.
        "tiktok": {**base, "schedulingType": "notification",
                   "channelId": chans["tiktok"]["id"], "text": post["caption_tiktok"],
                   "assets": [{"image": {"url": u}} for u in image_urls(week, post, "tiktok")],
                   "metadata": {"tiktok": {"title": title[:90]}}},
        "instagram": {**base, "channelId": chans["instagram"]["id"], "text": post["caption_instagram"],
                      "assets": [{"image": {"url": u}} for u in image_urls(week, post, "instagram")[:10]],
                      "metadata": {"instagram": {"type": "post", "shouldShareToFeed": True}}},
    }


CREATE = """mutation($input: CreatePostInput!) { createPost(input: $input) {
  ... on PostActionSuccess { post { id dueAt status } }
  ... on MutationError { message } } }"""


def send(week, draft=False, dry=False):
    plan = json.loads((ROOT / week / "plan.json").read_text())
    log_path = ROOT / week / "buffer.json"
    log = json.loads(log_path.read_text()) if log_path.exists() else {}
    chans = check() if not dry else {"tiktok": {"id": "TIKTOK"}, "instagram": {"id": "INSTAGRAM"}}
    for post in plan["posts"]:
        for service, inp in post_inputs(week, post, chans, draft).items():
            key = f"{post['id']}/{service}"
            if key in log:
                print(f"skip {key}: already in Buffer ({log[key]['id']})")
                continue
            if dry:
                print(f"{key}: {inp['dueAt']} · {len(inp['assets'])} images · {inp['text'][:60]!r}")
                continue
            bad = [a["image"]["url"] for a in inp["assets"] if not url_ok(a["image"]["url"])]
            if bad:
                sys.exit(f"{key}: images not reachable yet, run upload first: {bad[0]}")
            res = gql(CREATE, {"input": inp})["createPost"]
            if "message" in res:
                print(f"FAILED {key}: {res['message']}")
                continue
            log[key] = res["post"]
            log_path.write_text(json.dumps(log, indent=2))
            print(f"{'drafted' if draft else 'scheduled'} {key} for {res['post']['dueAt']}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    week = sys.argv[2] if len(sys.argv) > 2 else "weeks/2026-11-02"
    if cmd == "check":
        check()
    elif cmd == "upload":
        upload(week)
    elif cmd == "dry-run":
        send(week, dry=True)
    elif cmd in ("schedule", "draft"):
        send(week, draft=cmd == "draft")
    else:
        sys.exit(__doc__)
