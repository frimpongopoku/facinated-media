"""Read the facinated.com catalog into catalog.json and download product images.

The website is the source of truth: every product page carries schema.org
Product JSON-LD (name, price, images, availability), so we read that.
"""
import json
import pathlib
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor

SITE = "https://facinated.com"
ROOT = pathlib.Path(__file__).parent
IMG_DIR = ROOT / "assets" / "products"
UA = {"User-Agent": "Mozilla/5.0 (facinated-content-engine)"}


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def product_links(html):
    slugs = re.findall(r'href="/products/([^"?#]+)"', html)
    return sorted(set(slugs))


def collection_members(html, collection):
    page = get(f"{SITE}/collections/{collection}").decode("utf-8", "replace")
    return set(product_links(page))


def read_product(slug):
    html = get(f"{SITE}/products/{slug}").decode("utf-8", "replace")
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not m:
        return None
    data = json.loads(m.group(1))
    offer = data.get("offers") or {}
    images = data.get("image") or []
    if isinstance(images, str):
        images = [images]
    return {
        "slug": slug,
        "name": data.get("name", slug).strip(),
        "description": (data.get("description") or "").strip(),
        "price": offer.get("price"),
        "currency": offer.get("priceCurrency", "GHS"),
        "availability": (offer.get("availability") or "").rsplit("/", 1)[-1],
        "url": data.get("url") or f"{SITE}/products/{slug}",
        "images": images,
    }


def download_images(product):
    local = []
    for i, url in enumerate(product["images"][:4]):
        ext = url.rsplit(".", 1)[-1].split("?")[0] or "webp"
        path = IMG_DIR / f"{product['slug']}-{i}.{ext}"
        if not path.exists():
            path.write_bytes(get(url))
        local.append(str(path.relative_to(ROOT)))
    product["local_images"] = local
    return product


def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    home = get(SITE).decode("utf-8", "replace")
    collections = sorted(set(re.findall(r'href="/collections/([^"?#]+)"', home)))
    slugs = set(product_links(home))
    membership = {}
    for c in collections:
        members = collection_members(home, c)
        slugs |= members
        for s in members:
            membership.setdefault(s, []).append(c)

    with ThreadPoolExecutor(8) as pool:
        products = [p for p in pool.map(read_product, sorted(slugs)) if p]
        products = [p for p in pool.map(download_images, products) if p["images"]]
    for p in products:
        p["collections"] = membership.get(p["slug"], [])

    (ROOT / "catalog.json").write_text(json.dumps(products, indent=2, ensure_ascii=False))
    print(f"{len(products)} products, {sum(len(p['local_images']) for p in products)} images")


if __name__ == "__main__":
    main()
