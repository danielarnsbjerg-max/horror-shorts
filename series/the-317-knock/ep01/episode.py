"""The 3:17 Knock - Part 1/7.

Words wrapped in *asterisks* are highlighted yellow in the captions.
Character dicts: x, feet (screen px), s (scale), view front/back, expr neutral/scared/terrified,
tremble 0..1, turn 0..1 (back->front head turn), arm 0..1. Any value may be a (start, end) tuple
that is eased over the beat.
"""
BG = "../assets/bg/"

EPISODE = {
    "part": 1, "parts": 7, "tag": "FLOOR 4",
    "clock_target": "03:17:00",
    "vo_dir": "vo",
    "scenes": {
        "exterior": {"bg": BG + "exterior.png"},
        "bedroom": {"bg": BG + "bedroom.png", "cam": {"zoom": (1.0, 1.1), "x": 0.52}},
        "frontdoor": {"bg": BG + "frontdoor.png", "cam": {"zoom": (1.0, 1.15), "x": 0.46}},
        "corridor": {"bg": BG + "corridor.png", "fx": "peephole", "flicker": True},
        "closet": {"bg": BG + "closet.png", "cam": {"zoom": (1.0, 1.15), "x": 0.41, "y": 0.55}},
        "bed": {"bg": BG + "bed.png", "cam": {"zoom": (1.0, 1.2), "x": 0.55, "y": 0.55}},
    },
    "beats": [
        {"scene": "exterior", "vo": "00", "text": "Imagine you live *alone*... on the *fourth* *floor*.",
         "cam": {"zoom": (1.0, 1.5), "x": (0.5, 0.465), "y": (0.5, 0.43)}},
        {"scene": "bedroom", "vo": "01", "text": "Every night, at exactly *3:17*... someone *knocks* on your door.",
         "char": {"x": 600, "feet": 1650, "s": 1.6}},
        {"scene": "frontdoor", "vo": "02", "text": "You've checked the *peephole* a hundred times.",
         "char": {"x": 520, "feet": 1690, "s": 1.75, "view": "back", "turn": 0.0, "arm": (0.0, 0.9)}},
        {"scene": "corridor", "vo": "03", "text": "*Nobody* is ever there.", "pad": 0.6},
        {"scene": "bedroom", "vo": "04", "text": "Tonight, you stay *awake*. *Waiting*.", "hold": 1.4,
         "cam": {"zoom": (1.05, 1.25), "x": 0.55},
         "char": {"x": 600, "feet": 1650, "s": (1.6, 1.75), "expr": "neutral"}},
        {"scene": "bedroom", "knock": 3, "clock_hit": True,
         "cam": {"zoom": 1.25, "x": 0.55}, "char": {"x": 600, "feet": 1650, "s": 1.75, "expr": "scared"}},
        {"scene": "bedroom", "vo": "05", "text": "*3:17.* Right on *time*.",
         "cam": {"zoom": (1.25, 1.3), "x": 0.55}, "char": {"x": 600, "feet": 1650, "s": 1.75, "expr": "scared", "tremble": 0.3}},
        {"scene": "frontdoor", "vo": "06", "text": "But it's not coming from the *front* *door*...",
         "cam": {"zoom": (1.1, 1.3), "x": 0.46}},
        {"scene": "closet", "knock": 3},
        {"scene": "closet", "vo": "07", "text": "It's coming from your *closet*.",
         "char": {"x": 300, "feet": 1710, "s": 1.85, "view": "back", "turn": 0.0, "tremble": 0.5}},
        {"scene": "closet", "vo": "08", "text": "Then you hear a voice. *Your* *voice*.",
         "cam": {"zoom": (1.15, 1.3), "x": 0.41, "y": 0.6},
         "char": {"x": 300, "feet": 1710, "s": 1.85, "view": "back", "turn": (0.0, 0.5), "expr": "scared", "tremble": 0.6}},
        {"scene": "closet", "vo": "09", "text": "\"Let me *out*... he's in your *bed*.\"", "whisper": True, "pad": 0.7,
         "cam": {"zoom": (1.3, 1.7), "x": 0.41, "y": (0.6, 0.75)}},
        {"scene": "bed", "vo": "10", "text": "You slowly *turn* *around*...", "heartbeat": True, "pad": 0.5,
         "char": {"x": 860, "feet": 2350, "s": 2.4, "view": "back", "turn": (0.0, 1.0), "expr": "terrified", "tremble": 0.4}},
        {"scene": "bed", "vo": "11", "text": "and the *blanket*... starts to *breathe*.", "heartbeat": True, "pulse": 0.025, "pad": 1.2,
         "cam": {"zoom": (1.15, 1.45), "x": 0.5, "y": 0.6}},
        {"scene": "bedroom", "vo": "12", "text": "So what do you do?", "choice": True, "hold": 2.8,
         "cam": {"zoom": (1.0, 1.08), "x": 0.5, "y": 0.55}},
    ],
    "choice": {"question": "THE CLOSET,\nOR THE BLANKET?", "a": "CLOSET", "b": "BLANKET", "a_at": 0.45, "b_at": 0.8},
    "countdown": {"before": "NEXT KNOCK IN", "after": "IT LEAVES IN", "after_secs": 17 * 60},
    "handle": "@midnightstories2255",
    "tail": 0.6,
}
