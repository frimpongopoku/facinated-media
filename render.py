"""Render a week of posts (weeks/<week>/plan.json) into slide images.

Each post is a list of slides; each slide has a `type` (cover, product, grid,
cta) and refers to products by slug from catalog.json. Every slide is rendered
twice: 9:16 for TikTok photo mode and 4:5 for Instagram carousels.

    python3 render.py weeks/2026-11-02
"""
import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).parent
FONTS = ROOT / "assets" / "fonts"

CREAM = (243, 235, 224)
WINE = (110, 26, 46)
INK = (42, 27, 23)
GOLD = (176, 138, 79)
WHITE = (255, 255, 255)

SIZES = {"tiktok": (1080, 1920), "instagram": (1080, 1350)}


def font(name, size):
    return ImageFont.truetype(str(FONTS / f"{name}.ttf"), size)


SERIF = "playfair-display-400-normal"
SERIF_BOLD = "playfair-display-700-normal"
SERIF_ITALIC = "playfair-display-400-italic"
SANS = "jost-400-normal"
SANS_MED = "jost-500-normal"
SANS_SEMI = "jost-600-normal"


def price(p):
    return f"GHS {int(p['price']):,}" if p.get("price") is not None else ""


def cover_fit(img, w, h, anchor_y=0.25):
    """Scale and crop to fill w x h; anchor_y keeps the hat (top of frame) in view."""
    img = img.convert("RGB")
    scale = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    left = (img.width - w) // 2
    top = round((img.height - h) * anchor_y)
    return img.crop((left, top, left + w, top + h))


def photo(slide, catalog):
    """A slide shows its product's photo, or an extra photo from extras/ when given."""
    if slide.get("photo"):
        return Image.open(ROOT / slide["photo"])
    p = catalog[slide["product"]]
    return Image.open(ROOT / p["local_images"][slide.get("image", 0)])


def wrap(draw, text, fnt, max_w):
    lines, line = [], ""
    for word in text.split(" "):
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=fnt) <= max_w or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def text_block(draw, xy, text, fnt, fill, max_w, line_gap=1.15, align="left"):
    x, y = xy
    for line in wrap(draw, text, fnt, max_w):
        lx = x if align == "left" else x + (max_w - draw.textlength(line, font=fnt)) / 2
        draw.text((lx, y), line, font=fnt, fill=fill)
        y += fnt.size * line_gap
    return y


def tracked(draw, xy, text, fnt, fill, spacing=4, align_w=None):
    """Letter-spaced small caps style label."""
    text = text.upper()
    total = sum(draw.textlength(c, font=fnt) + spacing for c in text) - spacing
    x, y = xy
    if align_w:
        x += (align_w - total) / 2
    for c in text:
        draw.text((x, y), c, font=fnt, fill=fill)
        x += draw.textlength(c, font=fnt) + spacing
    return total


def bottom_shade(img, start, strength=0.92):
    w, h = img.size
    shade = Image.new("L", (1, h), 0)
    for y in range(h):
        t = max(0.0, (y - start) / (h - start))
        shade.putpixel((0, y), int(255 * strength * min(1.0, t * 1.6) ** 1.1))
    shade = shade.resize((w, h))
    dark = Image.new("RGB", (w, h), (20, 10, 8))
    return Image.composite(dark, img, shade)


def wordmark(draw, w, y, fill):
    tracked(draw, (0, y), "facinated.com", font(SANS_MED, 26), fill, spacing=6, align_w=w)


def render_cover(slide, catalog, w, h):
    img = cover_fit(photo(slide, catalog), w, h)
    img = bottom_shade(img, int(h * 0.36))
    d = ImageDraw.Draw(img)
    pad = 80
    head = font(SERIF_BOLD, 92 if w / h < 0.7 else 80)
    lines = wrap(d, slide["headline"], head, w - 2 * pad)
    sub = slide.get("sub")
    sub_f = font(SERIF_ITALIC, 44)
    sub_lines = wrap(d, sub, sub_f, w - 2 * pad) if sub else []
    # Keep text clear of TikTok's bottom caption overlay.
    bottom = h - (380 if w / h < 0.7 else 150)
    block_h = len(lines) * head.size * 1.08 + len(sub_lines) * sub_f.size * 1.3 + 70
    y = bottom - block_h
    tracked(d, (pad, y), slide.get("kicker", "Facinated"), font(SANS_SEMI, 28), GOLD, spacing=7)
    y += 60
    for line in lines:
        d.text((pad, y), line, font=head, fill=WHITE)
        y += head.size * 1.08
    y += 14
    for line in sub_lines:
        d.text((pad, y), line, font=sub_f, fill=CREAM)
        y += sub_f.size * 1.3
    wordmark(d, w, 70, WHITE)
    return img


def render_product(slide, catalog, w, h):
    p = catalog.get(slide.get("product"), {})
    tall = w / h < 0.7
    band = 560 if tall else 300
    img = Image.new("RGB", (w, h), CREAM)
    img.paste(cover_fit(photo(slide, catalog), w, h - band), (0, 0))
    d = ImageDraw.Draw(img)
    pad = 80
    y = h - band + 48
    if slide.get("number"):
        r = 62
        cx, cy = w - pad - r, h - band - r // 2
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=WINE, outline=CREAM, width=6)
        n = str(slide["number"])
        nf = font(SERIF_BOLD, 76)
        d.text((cx - d.textlength(n, font=nf) / 2, cy - 52), n, font=nf, fill=CREAM)
    if slide.get("label"):
        tracked(d, (pad, y), slide["label"], font(SANS_SEMI, 26), GOLD, spacing=6)
        y += 52
    name_f = font(SERIF, 64 if tall else 56)
    y = text_block(d, (pad, y), slide.get("title") or p.get("name", "").title(), name_f, INK, w - 2 * pad - 140, 1.1)
    y += 10
    line = price(p) if slide.get("show_price", True) else ""
    if slide.get("note"):
        line = f"{line}  ·  {slide['note']}" if line else slide["note"]
    if line:
        d.text((pad, y), line, font=font(SANS_MED, 46), fill=WINE)
    return img


def render_grid(slide, catalog, w, h):
    tall = w / h < 0.7
    img = Image.new("RGB", (w, h), CREAM)
    d = ImageDraw.Draw(img)
    pad, gap = 60, 16
    top = 300 if tall else 230
    bottom = 260 if tall else 50
    cell_h = (h - top - bottom - gap) // 2
    cell_w = min((w - 2 * pad - gap) // 2, int(cell_h / 1.25))
    pad = (w - 2 * cell_w - gap) // 2
    for i, slug in enumerate(slide["products"][:4]):
        p = catalog[slug]
        x = pad + (i % 2) * (cell_w + gap)
        y = top + (i // 2) * (cell_h + gap)
        img.paste(cover_fit(Image.open(ROOT / p["local_images"][0]), cell_w, cell_h), (x, y))
    tracked(d, (0, 100 if tall else 70), slide.get("kicker", "Facinated"), font(SANS_SEMI, 26), GOLD, 7, w)
    text_block(d, (pad, (160 if tall else 120)), slide["headline"], font(SERIF_BOLD, 64 if tall else 56), INK, w - 2 * pad, 1.1, "center")
    if tall and slide.get("sub"):
        text_block(d, (pad, top + 2 * cell_h + gap + 50), slide["sub"], font(SERIF_ITALIC, 44), WINE, w - 2 * pad, 1.3, "center")
    return img


def render_cta(slide, catalog, w, h):
    img = Image.new("RGB", (w, h), WINE)
    d = ImageDraw.Draw(img)
    pad = 100
    tall = w / h < 0.7
    y = h * (0.30 if tall else 0.22)
    tracked(d, (0, y), slide.get("kicker", "Facinated"), font(SANS_SEMI, 28), GOLD, 7, w)
    y += 80
    y = text_block(d, (pad, y), slide["headline"], font(SERIF_BOLD, 84 if tall else 74), CREAM, w - 2 * pad, 1.1, "center")
    y += 40
    d.line((w / 2 - 60, y, w / 2 + 60, y), fill=GOLD, width=3)
    y += 50
    for line in slide.get("lines", []):
        y = text_block(d, (pad, y), line, font(SANS, 48), CREAM, w - 2 * pad, 1.35, "center") + 14
    wordmark(d, w, h - (420 if tall else 110), GOLD)
    return img


RENDERERS = {"cover": render_cover, "product": render_product, "grid": render_grid, "cta": render_cta}


def main(week_dir):
    week_dir = ROOT / week_dir
    catalog = {p["slug"]: p for p in json.loads((ROOT / "catalog.json").read_text())}
    plan = json.loads((week_dir / "plan.json").read_text())
    for post in plan["posts"]:
        for platform, (w, h) in SIZES.items():
            out = week_dir / post["id"] / platform
            out.mkdir(parents=True, exist_ok=True)
            for old in out.glob("*.jpg"):
                old.unlink()
            for i, slide in enumerate(post["slides"], 1):
                img = RENDERERS[slide["type"]](slide, catalog, w, h)
                img.save(out / f"{i:02d}.jpg", quality=90)
        print(f"rendered {post['id']}: {len(post['slides'])} slides")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "weeks/2026-11-02")
