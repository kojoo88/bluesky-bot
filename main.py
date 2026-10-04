import requests
import urllib3
import time
from datetime import datetime, timezone

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
            print(f"❌ လော့ဂ်အင်မအောင်မြင် — Status: {resp.status_code}")
            return None, None
        data = resp.json()
        print(f"✅ လော့ဂ်အင်အောင်မြင် — {HANDLE}")
        return data["accessJwt"], data["did"]
    except Exception as e:
        print(f"❌ အမှား: {e}")
        return None, None

def get_notifs(token):
    try:
        resp = requests.get(
            f"{BASE}/app.bsky.notification.listNotifications",
            headers={"Authorization": f"Bearer {token}"},
            params={"limit": 10}, verify=False, timeout=30
        )
        if resp.status_code != 200:
            print(f"⚠️ အကြောင်းကြားစာမဖတ်နိုင် — Status {resp.status_code}")
            return []
        return resp.json().get("notifications", [])
    except Exception as e:
        print(f"⚠️ ဖတ်ရန်အမှား: {e}")
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
    except Exception as e:
        print(f"❌ ပြန်ပို့ရန်အမှား: {e}")
        return False

print("🤖 Blue Sky Auto-Reply Bot — စတင်နေပြီ")

token, did = login()
if not token:
    print("\n❌ စကားဝှက်စစ်ဆေးပါ — App Password ဖြစ်ရမည်!")
    exit(1)

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
        
        reason = n.get("reason", "")
        if reason in ["reply", "mention"]:
            user = n["author"]["handle"]
            msg_text = n["record"]["text"][:40]
            print(f"📩 {user}: {msg_text}")
            
            ok = send_reply(token, did, n["uri"], cid, REPLY_TEXT)
            if ok:
                print(f"✅ ပြန်ပေးပြီးပြီ → {user}\n")
    
    time.sleep(CHECK_INTERVAL)
