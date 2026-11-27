"""Midnight Stories agents (Instagram Graph API via graph.facebook.com; token is injected by the proxy).

  python3 tools/agents.py analytics        -> posts/analytics.json + hit/flop classification vs channel median
  python3 tools/agents.py comments         -> new comments on our posts that we haven't answered (JSON)
  python3 tools/agents.py reply ID "text"  -> reply to one comment
  python3 tools/agents.py votes SLUG a b   -> count keyword votes for a posted part
  python3 tools/agents.py research         -> outliers from strategy/niche_accounts.txt (needs business discovery permission)
"""
import json, os, statistics, sys, urllib.parse, urllib.request
G = "https://graph.facebook.com/v23.0"; IG = "17841469898518066"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def get(path, **q):
    url = f"{G}/{path}" + ("?" + urllib.parse.urlencode(q) if q else "")
    with urllib.request.urlopen(url) as r: return json.load(r)
def post(path, **data):
    req = urllib.request.Request(f"{G}/{path}", data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req) as r: return json.load(r)
def log(): return json.load(open(os.path.join(ROOT, "posts/log.json")))

def analytics():
    rows = {}
    for slug, mid in log().items():
        m = get(mid, fields="like_count,comments_count,timestamp,permalink")
        row = {"likes": m.get("like_count", 0), "comments": m.get("comments_count", 0), "posted": m["timestamp"], "url": m["permalink"]}
        try:  # needs instagram_manage_insights
            ins = get(f"{mid}/insights", metric="views,reach,shares,saved,total_interactions")
            row.update({d["name"]: d["values"][0]["value"] for d in ins.get("data", [])})
        except Exception: pass
        row["score"] = row.get("views") or (row["likes"] + 3 * row["comments"])
        rows[slug] = row
    med = statistics.median([r["score"] for r in rows.values()]) or 1
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    for r in rows.values():
        r["x_normal"] = round(r["score"] / med, 2)
        age_h = (now - datetime.datetime.fromisoformat(r["posted"].replace("+0000", "+00:00"))).total_seconds() / 3600
        r["age_h"] = round(age_h)
        r["verdict"] = "too_new" if age_h < 48 else "hit" if r["x_normal"] >= 3 else "flop" if r["x_normal"] <= 0.4 else "normal"
    json.dump(rows, open(os.path.join(ROOT, "posts/analytics.json"), "w"), indent=1)
    print(json.dumps(rows, indent=1))

def comments():
    out = []
    for slug, mid in log().items():
        for c in get(f"{mid}/comments", fields="id,text,username,timestamp,replies{username}", limit=100).get("data", []):
            mine = any(r.get("username") == "midnightstories2255" for r in c.get("replies", {}).get("data", []))
            if not mine and c.get("username") != "midnightstories2255":
                out.append({"slug": slug, "id": c["id"], "text": c["text"], "user": c.get("username"), "time": c["timestamp"]})
    print(json.dumps(out, indent=1, ensure_ascii=False))

def votes(slug, a, b):
    mid = log()[slug]; n = {a: 0, b: 0}
    for c in get(f"{mid}/comments", fields="text", limit=100).get("data", []):
        t = c["text"].lower()
        for k in n:
            if k.lower() in t: n[k] += 1
    print(json.dumps(n))

def research():
    accts = [l.strip().lstrip("@") for l in open(os.path.join(ROOT, "strategy/niche_accounts.txt")) if l.strip() and not l.startswith("#")]
    found = []
    for u in accts:
        try:
            d = get(IG, fields=f"business_discovery.username({u}){{username,followers_count,media.limit(30){{caption,like_count,comments_count,media_product_type,permalink,timestamp}}}}")["business_discovery"]
        except Exception as e:
            print(f"skip {u}: {e}", file=sys.stderr); continue
        media = [m for m in d.get("media", {}).get("data", []) if m.get("media_product_type") == "REELS"]
        if not media: continue
        med = statistics.median([m.get("like_count", 0) for m in media]) or 1
        for m in media:
            x = m.get("like_count", 0) / med
            if x >= 3: found.append({"account": u, "x_normal": round(x, 1), "hook": (m.get("caption") or "").split("\n")[0][:140], "url": m["permalink"]})
    found.sort(key=lambda r: -r["x_normal"])
    print(json.dumps(found[:20], indent=1, ensure_ascii=False))

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "reply": print(post(f"{sys.argv[2]}/replies", message=sys.argv[3]))
    elif cmd == "votes": votes(*sys.argv[2:5])
    else: globals()[cmd]()
