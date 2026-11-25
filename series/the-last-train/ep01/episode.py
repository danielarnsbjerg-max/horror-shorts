"""The Last Train - Part 1/7."""
BG = "../assets/bg/"
EPISODE = {
    "part": 1, "parts": 7, "tag": "STATION ???",
    "clock_target": "01:13:00", "vo_dir": "vo",
    "countdown": {"before": "NEXT STOP IN", "after": "DOORS CLOSE IN", "after_secs": 30},
    "handle": "@midnightstories2255",
    "scenes": {
        "train": {"bg": BG + "train_empty.png", "cam": {"zoom": (1.0, 1.15), "x": 0.5}, "flicker": True},
        "passengers": {"bg": BG + "passengers.png", "cam": {"zoom": (1.0, 1.2), "x": 0.5}, "flicker": True},
        "platform": {"bg": BG + "platform.png", "cam": {"zoom": (1.0, 1.2), "x": 0.47}},
        "window": {"bg": BG + "window.png", "cam": {"zoom": (1.0, 1.6), "x": (0.55, 0.62), "y": 0.5}},
    },
    "beats": [
        {"scene": "train", "vo": "00", "text": "Imagine you fall asleep on the *last* *train* home."},
        {"scene": "passengers", "vo": "01", "text": "When you wake up... the carriage is *full*.",
         "char": {"x": 540, "feet": 1700, "s": 1.7, "view": "back", "turn": 0.0}},
        {"scene": "passengers", "vo": "02", "text": "Every passenger is *staring* straight ahead.", "cam": {"zoom": (1.1, 1.35), "x": 0.5}},
        {"scene": "passengers", "vo": "03", "text": "Nobody *blinks*. Nobody *breathes*.", "cam": {"zoom": (1.4, 1.7), "x": 0.28, "y": 0.45}},
        {"scene": "window", "vo": "04", "text": "Outside the window, there's no *city*. Just black... and someone standing on the *tracks*.", "pad": 0.6},
        {"scene": "platform", "knock": 2, "clock_hit": True},
        {"scene": "platform", "vo": "05", "text": "The train stops at a station that *isn't* on the *map*.",
         "char": {"x": 540, "feet": 1700, "s": 1.7, "view": "back", "turn": 0.0, "tremble": 0.2}},
        {"scene": "platform", "vo": "06", "text": "The doors open. You have *thirty* *seconds*.", "cam": {"zoom": (1.2, 1.4), "x": 0.47}},
        {"scene": "passengers", "vo": "07", "text": "Then every passenger *turns* their head... towards *you*.", "heartbeat": True,
         "cam": {"zoom": (1.0, 1.4), "x": 0.5},
         "char": {"x": 830, "feet": 2300, "s": 2.3, "view": "back", "turn": (0.0, 1.0), "expr": "terrified", "tremble": 0.4}},
        {"scene": "passengers", "vo": "08", "text": "\"This is your *stop*.\"", "whisper": True, "heartbeat": True, "pad": 0.8,
         "cam": {"zoom": (1.6, 2.0), "x": 0.72, "y": 0.4}},
        {"scene": "platform", "vo": "09", "text": "So what do you do?", "choice": True, "hold": 2.8, "cam": {"zoom": (1.0, 1.08), "x": 0.47}},
    ],
    "choice": {"question": "GET OFF,\nOR STAY ON?", "a": "GET OFF", "b": "STAY", "a_at": 0.45, "b_at": 0.85},
    "tail": 0.6,
}
