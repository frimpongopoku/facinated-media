"""Helpers for planning a week: which week is next, what was featured lately,
and a strict check of a plan.json before anything is rendered or posted.

    python3 week.py next              # prints the week folder to plan, or "none"
    python3 week.py history           # products and formats used in recent weeks
    python3 week.py validate weeks/2026-11-09
"""
import datetime as dt
import json
import pathlib
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).parent
WEEKS = ROOT / "weeks"
SLIDE_TYPES = {"cover", "product", "grid", "cta"}
MAX_SLIDES = 10  # Instagram carousel limit


def next_week(today=None):
    """The Monday after today, unless that week already has a plan."""
    today = today or dt.date.today()
    monday = today + dt.timedelta(days=7 - today.weekday())
    folder = WEEKS / monday.isoformat()
    return None if (folder / "plan.json").exists() else f"weeks/{monday.isoformat()}"


def plans(limit=4):
    folders = sorted(p for p in WEEKS.iterdir() if (p / "plan.json").exists())
    return [json.loads((p / "plan.json").read_text()) for p in folders[-limit:]]


def history():
    used, formats = Counter(), Counter()
    for plan in plans():
        for post in plan["posts"]:
            formats[post["format"]] += 1
            for s in post["slides"]:
                for slug in [s.get("product"), *s.get("products", [])]:
                    if slug:
                        used[slug] += 1
    catalog = json.loads((ROOT / "catalog.json").read_text())
    print("Formats used in the last 4 weeks:", dict(formats))
    print("\nTimes each product appeared in the last 4 weeks (0 = never featured):")
    for p in sorted(catalog, key=lambda p: used[p["slug"]]):
        print(f"  {used[p['slug']]:2}  {p['slug']:40} {p['name']} · GHS {p['price']} · {p['availability']}")


def validate(week):
    folder = ROOT / week
    plan = json.loads((folder / "plan.json").read_text())
    slugs = {p["slug"] for p in json.loads((ROOT / "catalog.json").read_text())}
    start = dt.date.fromisoformat(plan["week"])
    problems = []
    if folder.name != plan["week"] or start.weekday() != 0:
        problems.append("plan.week must equal the folder name and be a Monday")
    ids = [p["id"] for p in plan["posts"]]
    if len(ids) != len(set(ids)):
        problems.append("post ids must be unique")
    for post in plan["posts"]:
        where = post.get("id", "?")
        for field in ("id", "date", "time", "format", "goal", "slides", "caption_tiktok", "caption_instagram"):
            if not post.get(field):
                problems.append(f"{where}: missing {field}")
        day = dt.date.fromisoformat(post["date"])
        if not start <= day <= start + dt.timedelta(days=6):
            problems.append(f"{where}: date {day} is outside the week")
        hh, _, mm = post["time"].partition(":")
        if not (hh.isdigit() and mm.isdigit() and 0 <= int(hh) < 24 and 0 <= int(mm) < 60):
            problems.append(f"{where}: time must be HH:MM")
        slides = post["slides"]
        if not 3 <= len(slides) <= MAX_SLIDES:
            problems.append(f"{where}: needs 3-{MAX_SLIDES} slides")
        if slides and slides[0]["type"] != "cover":
            problems.append(f"{where}: first slide must be a cover")
        for i, s in enumerate(slides, 1):
            if s["type"] not in SLIDE_TYPES:
                problems.append(f"{where} slide {i}: unknown type {s['type']}")
            for slug in [s.get("product"), *s.get("products", [])]:
                if slug and slug not in slugs:
                    problems.append(f"{where} slide {i}: unknown product {slug}")
            if s["type"] in ("cover", "product") and not (s.get("product") or s.get("photo")):
                problems.append(f"{where} slide {i}: {s['type']} needs a product or a photo")
            if s.get("photo") and not (ROOT / s["photo"]).is_file():
                problems.append(f"{where} slide {i}: photo {s['photo']} not found")
            if s["type"] == "product" and s.get("photo") and not (s.get("product") or s.get("title")):
                problems.append(f"{where} slide {i}: an extra photo needs a title")
            if s["type"] == "grid" and len(s.get("products", [])) != 4:
                problems.append(f"{where} slide {i}: grid needs exactly 4 products")
            if s["type"] in ("cover", "grid", "cta") and not s.get("headline"):
                problems.append(f"{where} slide {i}: {s['type']} needs a headline")
            text = json.dumps(s, ensure_ascii=False)
            for bad in ("➜", "→", "₵"):
                if bad in text:
                    problems.append(f"{where} slide {i}: '{bad}' is not in the slide fonts")
        cover = next((s for s in slides if s["type"] == "cover"), {})
        if len(cover.get("headline", "")) > 90:
            problems.append(f"{where}: cover headline over 90 characters (TikTok title limit)")
        if len(post.get("caption_tiktok", "")) > 2000:
            problems.append(f"{where}: TikTok caption too long")
        if len(post.get("caption_instagram", "")) > 2100:
            problems.append(f"{where}: Instagram caption too long")
        if post.get("caption_instagram", "").count("#") > 30:
            problems.append(f"{where}: Instagram allows at most 30 hashtags")
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print(f"{week}: plan OK ({len(plan['posts'])} posts)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "next"
    if cmd == "next":
        print(next_week() or "none")
    elif cmd == "history":
        history()
    elif cmd == "validate":
        validate(sys.argv[2])
    else:
        sys.exit(__doc__)
