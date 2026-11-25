#!/usr/bin/env bash
# Usage: posts/publish_ig.sh <slug>   (posts/<slug>.mp4 must be pushed to main; caption from posts/captions.json)
set -e
IG=17841469898518066; G=https://graph.facebook.com/v23.0
SLUG="$1"; URL="https://raw.githubusercontent.com/danielarnsbjerg-max/horror-shorts/main/posts/$SLUG.mp4"
CAP=$(python3 -c "import json,sys;print(json.load(open('$(dirname "$0")/captions.json'))[sys.argv[1]])" "$SLUG")
C=$(curl -s -X POST "$G/$IG/media" --form-string media_type=REELS --form-string "video_url=$URL" --form-string share_to_feed=true --form-string "caption=$CAP" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
for i in $(seq 1 40); do S=$(curl -s "$G/$C?fields=status_code" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status_code'))"); [ "$S" = FINISHED ] && break; [ "$S" = ERROR ] && { echo "processing error"; exit 1; }; sleep 10; done
M=$(curl -s -X POST "$G/$IG/media_publish" --form-string "creation_id=$C" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -s "$G/$M?fields=permalink"; echo
