# Strategy brain (used by the daily production run)

Pipeline (inspired by the "content agent" reel):
1. **Research agent** – `tools/agents.py research`: last 30 reels of each account in `niche_accounts.txt`, keeps outliers (≥3× the account's normal). *Needs the token to have business-discovery access (instagram_manage_insights + pages_read_engagement).*
2. **Hook agent** – saves how each outlier starts into `hook_bank.md`.
3. **Strategy agent** – reads `content_map.md` + `lessons.md` + votes and picks today's angle/hook for the scheduled part.
4. **Script agent** – writes the part with a hook pattern that has already won.
5. **Story check** (our "fact check") – continuity with the bible and previous parts, rules of the entity respected, choice is a real dilemma.
6. **Video agent** – voice (ElevenLabs Adam Deep), frames (low-poly + accent grade), captions, sound.
7. **Frame check** – render `--preview` stills of every beat; fix anything broken (cut-off text, character floating, black frames) before publishing.
8. **Cover + caption** – cover = cold-open frame (thumb_offset 600 ms); caption = hook + vote CTA + "send this to…" + hashtags.
9. **Publish** – 18:00 and 21:00 Copenhagen time (Instagram automatic, TikTok manual for now).
10. **Reply agent** – `tools/agents.py comments` → reply in character, short, with a nudge to the next part.
11. **Analytics agent** – `tools/agents.py analytics` (after 48 h): hit ≥3× normal → hook agent remakes it with 3 new hooks; flop ≤0.4× → lesson agent writes ONE lesson into `lessons.md`.
