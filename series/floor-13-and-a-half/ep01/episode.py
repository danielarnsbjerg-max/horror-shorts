"""Floor 13 1/2 - Part 1/7."""
BG = "../assets/bg/"
EPISODE = {
    "part": 1, "parts": 7, "tag": "FLOOR 13½",
    "clock_target": "00:00:00", "vo_dir": "vo",
    "countdown": {"label": "OXYGEN", "percent": 92, "rate": 0.3},
    "handle": "@midnightstories2255",
    "grade": "accent",
    "scenes": {
        "elevator": {"bg": BG + "elevator.png", "cam": {"zoom": (1.0, 1.12), "x": 0.5}, "flicker": True},
        "hatch": {"bg": BG + "hatch.png", "cam": {"zoom": (1.0, 1.3), "x": 0.45, "y": 0.35}, "flicker": True},
        "hallway": {"bg": BG + "hallway.png", "cam": {"zoom": (1.0, 1.25), "x": 0.5}},
        "hand": {"bg": BG + "hand.png", "cam": {"zoom": (1.0, 1.5), "x": 0.5, "y": 0.45}},
    },
    "beats": [
        {"scene": "elevator", "vo": "00", "text": "Imagine you're *alone* in an elevator, late at night.",
         "char": {"x": 540, "feet": 1690, "s": 1.65}},
        {"scene": "elevator", "vo": "01", "text": "It stops between floor *thirteen* and *fourteen*.",
         "char": {"x": 540, "feet": 1690, "s": 1.65, "expr": "scared", "tremble": 0.2}},
        {"scene": "elevator", "vo": "02", "text": "The display says... *thirteen* and a *half*.", "card": {"type": "display", "text": "13½"}},
        {"scene": "elevator", "vo": "03", "text": "You press the *alarm*. Nothing.", "pad": 0.5,
         "char": {"x": 540, "feet": 1690, "s": 1.65, "view": "back", "turn": 0.0, "arm": (0.0, 0.9)}},
        {"scene": "hatch", "knock": 3, "clock_hit": True},
        {"scene": "hatch", "vo": "04", "text": "Then something *knocks* on the roof *hatch*."},
        {"scene": "hatch", "vo": "05", "text": "Three times. *Slow*. *Patient*.", "cam": {"zoom": (1.3, 1.6), "x": 0.45, "y": 0.3}},
        {"scene": "hallway", "vo": "06", "text": "The doors slide open a few inches... and there's *no* *wall* behind them."},
        {"scene": "hallway", "vo": "07", "text": "Just a *hallway* that shouldn't *exist*.", "cam": {"zoom": (1.2, 1.5), "x": 0.5},
         "char": {"x": 540, "feet": 1730, "s": 1.8, "view": "back", "turn": 0.0, "tremble": 0.3}},
        {"scene": "hand", "vo": "08", "text": "Then a *hand* curls around the door... and holds it *open* for you.", "heartbeat": True, "pad": 0.8},
        {"scene": "hallway", "vo": "09", "text": "So what do you do?", "choice": True, "hold": 2.8, "cam": {"zoom": (1.0, 1.08), "x": 0.5}},
    ],
    "choice": {"question": "THE HATCH,\nOR THE HALLWAY?", "a": "HATCH", "b": "HALLWAY", "a_at": 0.45, "b_at": 0.85},
    "tail": 0.6,
}
