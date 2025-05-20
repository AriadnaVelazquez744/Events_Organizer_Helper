
# scraper.py
import re
from bs4 import BeautifulSoup
import requests

def extract_number(text):
    match = re.search(r'\d+', text.replace(',', ''))
    return int(match.group()) if match else None

def extract_price(text):
    match = re.search(r'[\$€£]\s?(\d+[,\d]*)', text)
    return float(match.group(1).replace(',', '')) if match else None

def scrape_page(url: str, context: dict = None) -> dict:
    response = requests.get(url)
    if response.status_code != 200:
        print(f"[SCRAPER] Página no encontrada (status: {response.status_code})")
        return {
            "title": f"{response.status_code} - {url}",
            "url": url,
            "entities": [],
            "timestamp": response.headers.get("Date"),
            "capacidad": None,
            "precio": None,
            "ciudad": None,
            "tipo_evento": "otro"
        }

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.title.string.strip() if soup.title else ""
    text = soup.get_text(separator=' ', strip=True)

    # Buscar capacidad estimada por keywords típicas
    capacidad = None
    capacity_match = re.search(r"up to (\d+)\s*(seats|standing|people)?", text, re.IGNORECASE)
    if capacity_match:
        capacidad = int(capacity_match.group(1))

    # Intentar inferir ciudad del texto o URL (fallback simple)
    ciudad = None
    if "London" in text:
        ciudad = "London"
    elif "london" in url.lower():
        ciudad = "London"

    # Inferir tipo de evento por palabras clave
    tipo_evento = "bar" if "bar" in text.lower() else "evento"

    return {
        "url": url,
        "title": title,
        "entities": [a.text for a in soup.find_all('a')][:5],
        "timestamp": response.headers.get("Date"),
        "capacidad": capacidad,
        "precio": extract_price(text),
        "ciudad": ciudad,
        "tipo_evento": tipo_evento
    }
