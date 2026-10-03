from flask import Flask
import requests
import urllib3
import time
import threading
from datetime import datetime, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

HANDLE = "kothet06.bsky.social"
PASSWORD = "37qw-44nv-gmak-v5bh"
CHECK_INTERVAL = 30
REPLY_TEXT = "မင်္ဂလာပါ 😊 မက်ဆေ့ချ်လက်ခံရရှိပါတယ်!\n\nကျွန်တော်အလုပ်လုပ်နေဆဲပါ 💙"

BASE = "https://bsky.social/xrpc"
last_seen = set()

def login():
    try:
        resp = requests.post(
            f"{BASE}/com.atproto.server.createSession",
            json={"identifier": HANDLE, "password": PASSWORD},
            verify=False, timeout=30
        )
        if resp.status_code != 200:
            return None, None
        data = resp.json()
        return data["accessJwt"], data["did"]
    except:
        return None, None

def get_notifs(token):
    try:
        resp = requests.get(
            f"{BASE}/app.bsky.notification.listNotifications",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 10}, verify=False, timeout=30
        )
        return resp.json().get("notifications", []) if resp.status_code==200 else []
    except:
        return []

def send_reply(token, did, ref_uri, ref_cid, text):
    try:
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        resp = requests.post(
            f"{BASE}/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": now,
                    "reply": {
                        "root": {"uri": ref_uri, "cid": ref_cid},
                        "parent": {"uri": ref_uri, "cid": ref_cid}
                    }
                }
            }, verify=False, timeout=30
        )
        return resp.status_code == 200
    except:
        return False

@app.route('/')
def home():
    return "✅ BlueSky Bot — အလုပ်လုပ်နေပါတယ်! 💙"

def bot_loop():
    print("🤖 Blue Sky Auto-Reply Bot — Cloud Version")
    print("✅ 24/7 အလုပ်လုပ်နေမည်၊ ဖုန်းပိတ်လည်းရပ်မနေဘူး!\n")

    token, did = login()
    if not token:
        print("❌ လော့ဂ်အင်မရပါ — စကားဝှက်စစ်ဆေးပါ")
        return

    for n in get_notifs(token):
        last_seen.add(n["cid"])

    print("✅ စတင်စောင့်ကြည့်နေပြီ...\n")

    while True:
        token, did = login()
        if not token:
            time.sleep(10)
            continue
        
        for n in get_notifs(token):
            cid = n["cid"]
            if cid in last_seen:
                continue
            last_seen.add(cid)
            
            if n.get("reason") in ["reply", "mention"]:
                user = n["author"]["handle"]
                msg = n["record"]["text"][:40]
                print(f"📩 {user}: {msg}...")
                
                ok = send_reply(token, did, n["uri"], cid, REPLY_TEXT)
                if ok:
                    print(f"✅ ပြန်ပေးပြီးပြီ → {user}\n")
        
        time.sleep(CHECK_INTERVAL)

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
