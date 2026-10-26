"""Build the weekly review page (docs/index.html, served by GitHub Pages) from
plan.json and the rendered slides, with web-sized copies of every image.

    python3 preview.py weeks/2026-11-02
"""
import datetime as dt
import html
import json
import pathlib
import shutil
import sys

from PIL import Image

ROOT = pathlib.Path(__file__).parent
WEB_WIDTH = 540


def esc(s):
    return html.escape(s, quote=True)


def web_copies(week_dir, post, platform, out_dir):
    paths = []
    for src in sorted((week_dir / post["id"] / platform).glob("*.jpg")):
        rel = pathlib.Path("img") / post["id"] / platform / src.name
        dst = out_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(src)
        im.resize((WEB_WIDTH, round(im.height * WEB_WIDTH / im.width)), Image.LANCZOS).save(dst, quality=80)
        paths.append(rel.as_posix())
    return paths


def caption_block(label, text, cid):
    return f"""
      <div class="cap">
        <div class="cap-head"><span class="eyebrow">{label}</span>
          <button type="button" class="copy" data-target="{cid}">Copy</button></div>
        <p id="{cid}" class="cap-text">{esc(text)}</p>
      </div>"""


def post_section(post, imgs):
    day = dt.date.fromisoformat(post["date"])
    strips = ""
    for platform, ratio in (("tiktok", "9 / 16"), ("instagram", "4 / 5")):
        cells = "".join(
            f'<img src="{p}" alt="{esc(post["format"])}, slide {i}" loading="lazy" style="aspect-ratio:{ratio}">'
            for i, p in enumerate(imgs[platform], 1)
        )
        hidden = "" if platform == "tiktok" else " hidden"
        strips += f'<div class="strip" data-platform="{platform}"{hidden}>{cells}</div>'
    return f"""
  <article class="post" id="{esc(post['id'])}">
    <header class="post-head">
      <div class="when">
        <span class="dow">{day.strftime('%A')}</span>
        <span class="date">{day.strftime('%-d %b')} · {post['time']} GMT</span>
      </div>
      <div class="what">
        <h2>{esc(post['format'])}</h2>
        <p class="goal">{esc(post['goal'])}</p>
      </div>
      <span class="count">{len(post['slides'])} slides</span>
    </header>
    {strips}
    <div class="caps">
      {caption_block("TikTok caption", post["caption_tiktok"], post["id"] + "-tt")}
      {caption_block("Instagram caption", post["caption_instagram"], post["id"] + "-ig")}
    </div>
  </article>"""


def main(week):
    week_dir = ROOT / week
    plan = json.loads((week_dir / "plan.json").read_text())
    out = ROOT / "docs"
    shutil.rmtree(out / "img", ignore_errors=True)
    out.mkdir(exist_ok=True)
    sections = []
    for post in plan["posts"]:
        imgs = {p: web_copies(week_dir, post, p, out) for p in ("tiktok", "instagram")}
        sections.append(post_section(post, imgs))
    start = dt.date.fromisoformat(plan["week"])
    end = start + dt.timedelta(days=6)
    brief = plan.get("film_brief")
    brief_html = ""
    if brief:
        shots = "".join(f"<li>{esc(s)}</li>" for s in brief["shots"])
        brief_html = f"""
  <section class="brief">
    <span class="eyebrow">{esc(brief['title'])}</span>
    <p>{esc(brief['why'])}</p>
    <ol>{shots}</ol>
  </section>"""
    page = TEMPLATE.format(
        range=f"{start.strftime('%-d')}–{end.strftime('%-d %B %Y')}",
        theme=esc(plan["theme"]),
        n=len(plan["posts"]),
        slides=sum(len(p["slides"]) for p in plan["posts"]),
        sections="".join(sections),
        brief=brief_html,
    )
    (out / "index.html").write_text(page)
    print(out / "index.html")


TEMPLATE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<title>Facinated Content Week</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,400&family=Jost:wght@400;500;600&display=swap">
<style>
/* Layout: a single editorial column, one day per section, slides as a swipeable strip like the phone will show them */
:root {{
  --bg: #f6efe6; --surface: #fffaf3; --ink: #2a1b17; --muted: #7a6559;
  --wine: #6e1a2e; --gold: #a07a3f; --line: #e4d6c6;
  --display: "Playfair Display", Georgia, "Times New Roman", serif;
  --body: "Jost", "Avenir Next", "Segoe UI", system-ui, sans-serif;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #1d1311; --surface: #2a1c19; --ink: #f3e9de; --muted: #bba79a;
  --wine: #e38aa0; --gold: #d2ac6c; --line: #3e2b26; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #1d1311; --surface: #2a1c19; --ink: #f3e9de; --muted: #bba79a;
  --wine: #e38aa0; --gold: #d2ac6c; --line: #3e2b26; color-scheme: dark }}
* {{ box-sizing: border-box }}
body {{ margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.55 var(--body); }}
.wrap {{ max-width: 980px; margin: 0 auto; padding-block: 48px 80px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
.eyebrow {{ font: 600 12px/1 var(--body); letter-spacing: .18em; text-transform: uppercase; color: var(--gold); }}
.masthead {{ display: grid; gap: 14px; padding-bottom: 32px; border-bottom: 1px solid var(--line); }}
h1 {{ font: 700 clamp(34px, 6vw, 56px)/1.05 var(--display); margin: 0; text-wrap: balance; }}
h1 em {{ font-weight: 400; color: var(--wine); }}
.lede {{ margin: 0; max-width: 62ch; color: var(--muted); font-size: 17px; }}
.toolbar {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 12px; margin-top: 8px; }}
.stats {{ color: var(--muted); font-size: 14px; }}
.toggle {{ display: inline-flex; border: 1px solid var(--line); border-radius: 999px; padding: 3px; background: var(--surface); }}
.toggle button {{ font: 500 14px var(--body); border: 0; background: none; color: var(--muted); padding: 7px 16px; border-radius: 999px; cursor: pointer; }}
.toggle button[aria-pressed="true"] {{ background: var(--wine); color: var(--surface); }}
.post {{ display: grid; gap: 20px; padding-block: 40px; border-bottom: 1px solid var(--line); }}
.post-head {{ display: grid; grid-template-columns: 150px 1fr auto; gap: 20px; align-items: start; }}
.when {{ display: grid; gap: 2px; }}
.dow {{ font: 700 26px/1.1 var(--display); color: var(--wine); }}
.date {{ font-size: 13px; color: var(--muted); font-variant-numeric: tabular-nums; }}
.what {{ min-width: 0; }}
h2 {{ font: 500 22px/1.2 var(--display); margin: 0 0 4px; }}
.goal {{ margin: 0; color: var(--muted); font-size: 15px; }}
.count {{ font-size: 13px; color: var(--muted); white-space: nowrap; padding-top: 6px; }}
.strip {{ display: flex; gap: 12px; overflow-x: auto; scroll-snap-type: x mandatory; padding-bottom: 8px; }}
.strip img {{ flex: 0 0 auto; height: 380px; width: auto; max-width: none; border-radius: 6px; scroll-snap-align: start; background: var(--line); }}
.strip[data-platform="instagram"] img {{ height: 320px; }}
.caps {{ display: grid; grid-template-columns: 1fr 1.4fr; gap: 16px; }}
.cap {{ background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px 18px; min-width: 0; }}
.cap-head {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
.cap-text {{ margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 15px; }}
.copy {{ font: 500 13px var(--body); color: var(--wine); background: none; border: 1px solid var(--line); border-radius: 999px; padding: 4px 12px; cursor: pointer; }}
button:focus-visible {{ outline: 2px solid var(--gold); outline-offset: 2px; }}
.brief {{ margin-top: 40px; padding: 28px; background: var(--surface); border: 1px solid var(--line); border-radius: 8px; display: grid; gap: 10px; }}
.brief p {{ margin: 0; color: var(--muted); max-width: 62ch; }}
.brief ol {{ margin: 0; padding-left: 22px; display: grid; gap: 6px; }}
.foot {{ margin-top: 32px; color: var(--muted); font-size: 14px; max-width: 62ch; }}
@media (max-width: 680px) {{
  .post-head {{ grid-template-columns: 1fr; gap: 6px; }}
  .count {{ padding-top: 0; }}
  .caps {{ grid-template-columns: 1fr; }}
  .strip img {{ height: 300px; }}
  .strip[data-platform="instagram"] img {{ height: 260px; }}
}}
</style>
<div class="wrap">
  <header class="masthead">
    <span class="eyebrow">Facinated · This week</span>
    <h1>Your week of posts, <em>{range}</em></h1>
    <p class="lede">{theme}. Each day posts to TikTok as a photo slideshow and to Instagram as a carousel. Swipe each row to see every slide.</p>
    <div class="toolbar">
      <span class="stats">{n} posts · {slides} slides each platform · made from your website photos</span>
      <div class="toggle" role="group" aria-label="Show slides for">
        <button type="button" id="show-tiktok" data-show="tiktok" aria-pressed="true">TikTok 9:16</button>
        <button type="button" id="show-instagram" data-show="instagram" aria-pressed="false">Instagram 4:5</button>
      </div>
    </div>
  </header>
  {sections}
  {brief}
  <p class="foot">These posts are scheduled in Buffer and go out automatically. To change something before it posts, edit or delete it in the Buffer app. To steer future weeks, add a line to NOTES.md in the facinated-media repo, or tell Claude.</p>
</div>
<script>
document.querySelectorAll('.toggle button').forEach(btn => btn.addEventListener('click', () => {{
  const show = btn.dataset.show;
  document.querySelectorAll('.toggle button').forEach(b => b.setAttribute('aria-pressed', String(b === btn)));
  document.querySelectorAll('.strip').forEach(s => {{ s.hidden = s.dataset.platform !== show; }});
}}));
document.querySelectorAll('.copy').forEach(btn => btn.addEventListener('click', () => {{
  const el = document.getElementById(btn.dataset.target);
  const done = () => {{ btn.textContent = 'Copied'; setTimeout(() => btn.textContent = 'Copy', 1600); }};
  const fallback = () => {{ const r = document.createRange(); r.selectNodeContents(el);
    const s = getSelection(); s.removeAllRanges(); s.addRange(r); btn.textContent = 'Selected'; }};
  try {{ navigator.clipboard.writeText(el.textContent).then(done, fallback); }} catch (e) {{ fallback(); }}
}}));
</script>
</html>
"""

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "weeks/2026-11-02")
