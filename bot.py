import requests
import time
import os
import json
import threading
from flask import Flask
from telegram import Bot

TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

bot = Bot(token=TOKEN)
app = Flask(__name__)

API_URL = "https://www.immobiliare.it/api-next/search-list/real-estates/"

PARAMS = {
    "fkRegione": 7,
    "fkProvincia": 28,
    "fkComune": 5726,
    "idContratto": 2,
    "idCategoria": 1,
    "criterio": "data",
    "ordine": "desc",
    "prezzoMinimo": 550,
    "prezzoMassimo": 900,
    "superficieMinima": 40,
    "localiMinimo": 2
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

SEEN_FILE = "seen.json"


def load_seen():
    try:
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    except:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def get_listings():
    r = requests.get(API_URL, params=PARAMS, headers=HEADERS)
    data = r.json()

    listings = []

    for item in data["results"]:
        listing = {
            "id": item["realEstate"]["id"],
            "title": item["realEstate"]["title"],
            "price": item["realEstate"]["price"]["value"],
            "surface": item["realEstate"].get("surface"),
            "link": "https://www.immobiliare.it" + item["realEstate"]["link"],
            "image": item["realEstate"]["images"][0]["url"]
            if item["realEstate"]["images"] else None
        }

        listings.append(listing)

    return listings


def send_listing(l):

    message = (
        f"🏠 {l['title']}\n"
        f"💶 {l['price']}€\n"
        f"📐 {l['surface']} m²\n"
        f"{l['link']}"
    )

    if l["image"]:
        bot.send_photo(chat_id=CHAT_ID, photo=l["image"], caption=message)
    else:
        bot.send_message(chat_id=CHAT_ID, text=message)


def bot_loop():

    seen = load_seen()

    while True:

        try:

            listings = get_listings()

            for l in listings:

                if str(l["id"]) not in seen:

                    send_listing(l)
                    seen.add(str(l["id"]))

            save_seen(seen)

            time.sleep(300)

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