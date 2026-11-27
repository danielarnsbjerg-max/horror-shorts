# Midnight Stories

Faceless animated horror shorts for Instagram Reels / TikTok / YouTube Shorts.
Each series runs 6–7 parts; every part ends with an A/B choice and the next part follows the majority.

## Layout
- `engine/` – renderer (HUD with clock, karaoke captions, cartoon "you" character, camera moves, sound design)
- `series/<name>/bible.md` – series bible: characters, rules, planned arc
- `series/<name>/assets/bg/` – background art (low-poly 3D style, generated with ElevenLabs image models)
- `series/<name>/epNN/episode.py` – beats, captions, character poses
- `series/<name>/epNN/vo/` – narration clips (ElevenLabs, voice "Adam – Deep & Confident")

## Render
```
pip install -r requirements.txt   # plus ffmpeg
python -m engine.render series/the-317-knock/ep01/episode.py out/ep01.mp4
python -m engine.render series/the-317-knock/ep01/episode.py out/preview.png --preview 2,10,20,30
```
Output: 1080x1920, 30 fps, H.264/AAC.

## Style rules
- EVERY part opens with an "Imagine…" hook line (part 1: "Imagine you…", later parts: "Imagine you just…" recap of the winning choice).
- Second person throughout, short sentences, a new caption every ~1 s.
- Captions: Inter Black, uppercase, 2–3 words, key words in yellow.
- HUD: ● PART n/7 + location tag + live clock counting toward the event time.
- 45–75 s per part; ends on a keyword choice card: question on top ("THE CLOSET, OR THE BLANKET?"), yellow + red keyword pills, then "FOLLOW FOR PART n+1 @handle". Viewers comment the keyword.
- HUD right side: yellow label + countdown (before the event "NEXT KNOCK IN", after it a stakes timer like "IT LEAVES IN").
- Colour grade: black / white / grey world with ONE accent colour (red-orange). Only the things we want the eye to follow keep colour: the hoodie, lights, the red carpet, the monster. Captions, HUD tags and the first choice pill use the same accent.
- Every part opens with a 1-1.5 s cold open of its scariest frame (also used as the cover).
- Always label as AI-generated when posting.
