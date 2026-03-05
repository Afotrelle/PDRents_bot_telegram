import requests
from bs4 import BeautifulSoup
import time
import json
import os
import threading
from telegram import Bot
from flask import Flask

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEARCH_URL = "https://www.immobiliare.it/affitto-case/padova/?criterio=data&ordine=desc&prezzoMinimo=550&prezzoMassimo=900&superficieMinima=40&localiMinimo=2&idMZona[0]=104&idMZona[1]=101&idMZona[2]=100&idMZona[3]=10387&idMZona[4]=10381&idMZona[5]=10382&idMZona[6]=10386&idMZona[7]=102&idMZona[8]=10384&idQuartiere[0]=385&idQuartiere[1]=325&idQuartiere[2]=408"

SEEN_FILE = "seen.json"

bot = Bot(token=TOKEN)
app = Flask(__name__)

headers = {"User-Agent": "Mozilla/5.0"}

def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def extract_listings():
    r = requests.get(SEARCH_URL, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    cards = soup.select("li.nd-list__item")
    listings = []

    for card in cards:
        link_tag = card.find("a", href=True)
        price_tag = card.select_one(".in-listingCardPrice")

        if not link_tag or not price_tag:
            continue

        link = link_tag["href"]
        price_text = price_tag.text.strip()

        try:
            price = int(price_text.replace("€", "").replace(".", "").strip())
        except:
            continue

        listings.append({"id": link, "price": price, "link": link})

    return listings

def bot_loop():
    while True:
        try:
            seen = load_seen()
            listings = extract_listings()

            for l in listings:
                if l["id"] not in seen:
                    message = f"🏠 Nuovo annuncio\n💶 {l['price']}€\n{l['link']}"
                    bot.send_message(chat_id=CHAT_ID, text=message)
                    seen.add(l["id"])

            save_seen(seen)
            time.sleep(600)

        except Exception as e:
            print("Errore:", e)
            time.sleep(60)

@app.route("/")
def home():
    return "Bot running"

if __name__ == "__main__":
    threading.Thread(target=bot_loop).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)