# Facinated social content engine

Plans, designs and schedules a week of TikTok and Instagram posts for
[facinated.com](https://facinated.com) every Monday. Posts go out through Buffer.

- **This week's posts:** https://frimpongopoku.github.io/facinated-media/
- **Steer future weeks:** edit [NOTES.md](NOTES.md)
- **Add your own photos:** upload to [extras/](extras/)

## How a week is made

```
python3 week.py next                    # which week to plan (or "none")
python3 scrape.py                       # refresh catalog.json from facinated.com
python3 week.py history                 # what was featured recently
# write weeks/<week>/plan.json following PLAYBOOK.md
python3 week.py validate weeks/<week>
python3 render.py weeks/<week>          # slides: 9:16 TikTok, 4:5 Instagram
python3 preview.py weeks/<week>         # review page in docs/
python3 publish.py upload weeks/<week>  # commit + push (images must be public)
python3 publish.py schedule weeks/<week>
```

Needs Python 3 with Pillow. The Buffer API key comes from `BUFFER_API_KEY`
(env or `.env`), or from a network secret that adds the header for api.buffer.com.
