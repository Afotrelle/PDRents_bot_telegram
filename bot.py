import requests
from bs4 import BeautifulSoup
import time
import json
import os
from telegram import Bot

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEARCH_URL = "https://www.immobiliare.it/affitto-case/padova/?criterio=data&ordine=desc&prezzoMinimo=550&prezzoMassimo=900&superficieMinima=40&localiMinimo=2&idMZona[0]=104&idMZona[1]=101&idMZona[2]=100&idMZona[3]=10387&idMZona[4]=10381&idMZona[5]=10382&idMZona[6]=10386&idMZona[7]=102&idMZona[8]=10384&idQuartiere[0]=385&idQuartiere[1]=325&idQuartiere[2]=408"

SEEN_FILE = "seen.json"

bot = Bot(token=TOKEN)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

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

        listings.append({
            "id": link,
            "price": price,
            "link": link
        })

    return listings

def check_new():
    seen = load_seen()
    listings = extract_listings()

    for l in listings:
        if l["id"] not in seen:
            message = (
                f"🏠 Nuovo annuncio\n"
                f"💶 {l['price']}€\n"
                f"{l['link']}"
            )

            bot.send_message(chat_id=CHAT_ID, text=message)
            seen.add(l["id"])

    save_seen(seen)

while True:
    try:
        check_new()
        time.sleep(600)  # ogni 10 minuti
    except Exception as e:
        print("Errore:", e)
        time.sleep(60)