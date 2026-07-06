import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime

BASE_URL = "https://www.olx.pl"
CATEGORY_URL = "https://www.olx.pl/oferty/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

data = []

# SZCZEGÓŁY OGŁOSZENIA (kategorie + lokalizacja)
def get_details(url):
    try:
        r = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        breadcrumbs = soup.find_all("li", {"data-testid": "breadcrumb-item"})

        items = []
        for b in breadcrumbs:
            a = b.find("a")
            if a:
                items.append(a.text.strip())

        # usuń "OLX"
        items = items[1:]

        categories = []
        locations = []

        for item in items:
            if " - " in item:
                name, loc = item.split(" - ", 1)
                categories.append(name)
                locations.append(loc)
            else:
                categories.append(item)

        # usuń duplikaty kategorii
        categories = list(dict.fromkeys(categories))

        region = None
        city = None
        district = None

        if len(locations) == 1:
            region = locations[0]

        elif len(locations) == 2:
            region = locations[0]
            city = locations[1]

        elif len(locations) >= 3:
            region = locations[0]
            city = locations[1]
            district = locations[2]

        return {
            "categories": categories,
            "category_path": " > ".join(categories),
            "region": region,
            "city": city,
            "district": district
        }

    except:
        return {
            "categories": [],
            "category_path": None,
            "region": None,
            "city": None,
            "district": None
        }


# LISTA OGŁOSZEŃ
def get_offers(page):
    url = f"{CATEGORY_URL}?page={page}"
    print(f"Pobieranie: {url}")

    r = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")

    offers = soup.find_all("div", {"data-cy": "l-card"})

    for offer in offers:

        # Tytuł
        title = None
        h4 = offer.find("h4")
        if h4:
            title = h4.text.strip()

        # Cena
        price_raw = None
        price_clean = None
        price_tag = offer.find("p", {"data-testid": "ad-price"})
        if price_tag:
            price_raw = price_tag.text.strip()
            price_clean = ''.join(ch for ch in price_raw if ch.isdigit() or ch == ',')

        is_negotiable = "negocjacji" in price_raw.lower() if price_raw else False

        # Data
        date_raw = None
        date = None
        loc_tag = offer.find("p", {"data-testid": "location-date"})

        if loc_tag:
            loc_text = loc_tag.text.strip()

            if " - " in loc_text:
                parts = loc_text.split(" - ", 1)
                raw_date = parts[1]
                date_raw = raw_date
                raw_date = raw_date.replace("Odświeżono dnia ", "")
                raw_date = raw_date.replace("Odświeżono ", "")

                # DZISIAJ
                if "Dzisiaj" in raw_date or "dzisiaj" in raw_date:
                    date = datetime.now().strftime("%Y-%m-%d")

                # NORMALNA DATA
                else:
                    months = {
                        "stycznia": "01", "lutego": "02", "marca": "03",
                        "kwietnia": "04", "maja": "05", "czerwca": "06",
                        "lipca": "07", "sierpnia": "08", "września": "09",
                        "października": "10", "listopada": "11", "grudnia": "12"
                    }

                    parts = raw_date.split()

                    if len(parts) >= 3:
                        day = parts[0]
                        month = months.get(parts[1], "XX")
                        year = parts[2]

                        date = f"{year}-{month}-{day.zfill(2)}"

        # Link
        link = None
        link_tag = offer.find("a")
        if link_tag:
            href = link_tag.get("href")

            if href.startswith("http"):
                link = href
            else:
                link = BASE_URL + href

        # SZCZEGÓŁY
        details = get_details(link)

        categories = details["categories"]
        category_path = details["category_path"]
        region = details["region"]
        city = details["city"]
        district = details["district"]

        data.append({
            "title": title,
            "price_raw": price_raw,
            "price": price_clean,
            "is_negotiable": is_negotiable,
            "date_raw": date_raw,
            "date": date,
            "category_path": category_path,
            "level1": categories[0] if len(categories) > 0 else None,
            "level2": categories[1] if len(categories) > 1 else None,
            "level3": categories[2] if len(categories) > 2 else None,
            "level4": categories[3] if len(categories) > 3 else None,
            "region": region,
            "city": city,
            "district": district,
            "link": link,
        })


# ile stron (max 25)
PAGES = 5

for page in range(1, PAGES + 1):
    get_offers(page)
    time.sleep(1)

# zapis
df = pd.DataFrame(data)
df.to_csv("olx_data_q.csv", index=False, encoding="utf-8-sig")

print("Zapisano do olx_data.csv")