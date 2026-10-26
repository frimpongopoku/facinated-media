# Facinated weekly content playbook

You are planning one week of social posts for **Facinated** (facinated.com), a
Ghanaian brand of fascinators, hatinators, hats, headbands and face nets made by
designer Stella. Every post goes to TikTok (@facinatedbystella, photo slideshow)
and Instagram (@akosuastellaofficial, carousel) through Buffer.

## Who we're talking to

Style-conscious Ghanaian women dressing for weddings, church, funerals,
engagements, naming ceremonies, graduations and other occasions. Many buy for
asoebi or family colours. Prices are in GHS (write "GHS 150"). Most pieces are
pre-order and can be made in any colour; a few are in stock.

## Voice

Warm, confident, celebratory, a little playful. Short sentences. Speak to her
directly ("your", "you"). A light Ghanaian touch is welcome but never forced.
Never invent discounts, deadlines, testimonials, customer names or stock levels.
Only mention a promotion if it's in NOTES.md.

Every Instagram caption ends with: order on WhatsApp **053 476 3923** and
**facinated.com (link in bio)**, then 8–12 hashtags. TikTok captions are one or
two lines plus 5–6 hashtags. Always include #facinated.

## The week

- 7 posts, one per day, Monday to Sunday.
- Times (Ghana time, GMT): weekdays 19:00, Saturday 10:00, Sunday 14:00, unless
  NOTES.md says otherwise.
- Mix formats; don't use any format more than twice a week. Formats that work:
  - **Poll**: "Which one for Saturday's wedding? 1, 2 or 3" (numbered product slides)
  - **Price reveal**: "Fascinators under GHS 100", "What GHS 200 gets you"
  - **Any colour**: made-to-order pieces, "send us your fabric"
  - **Piece of the week**: one product, use all its photos (`image` index)
  - **Collection edit**: bridal, church/Sunday best, funeral black & white,
    asoebi colours, statement hats, headbands, face nets, by colour family
  - **Ready now**: in-stock pieces only (availability InStock)
  - **Occasion**: tie to the season (see calendar below)
  - **Styling tip**: how to wear / pair a piece (cover + product slides + cta lines with tips)
- Feature products that have appeared least in recent weeks (`python3 week.py history`).
  Every product should get its turn. Don't feature the same product more than twice in a week.
- Use new photos in `extras/` when there are any (see extras/README.md); add each
  one you use to extras/USED.md with the week.

## Ghana calendar to plan around

- Wedding season peaks Nov–Dec and Easter–Aug; Saturdays are wedding days.
- Christmas (25 Dec), Watch Night / New Year (31 Dec–1 Jan): church outfits.
- Valentine's Day (14 Feb), Independence Day (6 Mar), Mother's Day (2nd Sunday of May),
  Father's Day, Easter (dates vary), Farmers' Day (1st Friday of Dec).
- Funerals are big weekend events: black, white, red-and-black pieces suit them.
  Keep funeral posts respectful.

## Slide types (plan.json)

Every post: first slide `cover`, last slide `cta`, 3–10 slides in total.

- `cover`: `product` (or `photo`), `kicker` (2–4 words), `headline` (max ~60 chars),
  `sub` (short line), optional `image` (photo index).
- `product`: `product`, optional `label` (2–3 words), `number` (for polls),
  `note` (shown after the price), `image`, `title` (overrides product name),
  `show_price` (default true). For an extras photo use `photo` and `title`.
- `grid`: `kicker`, `headline`, `products` (exactly 4), `sub`.
- `cta`: `kicker`, `headline`, `lines` (2–4 short lines).

Text rules: no arrows (➜ →) and no cedi sign (₵); the slide fonts don't have
them. Write "GHS 100" inside headlines so the amount never splits across lines.

Copy `weeks/2026-11-02/plan.json` for the exact shape. Each post has `id`
(`<n>-<day>-<slug>`), `date`, `time`, `format`, `goal`, `slides`,
`caption_tiktok`, `caption_instagram`. Add a `film_brief` with 3–4 simple
phone shots for Stella to film (optional for her).
