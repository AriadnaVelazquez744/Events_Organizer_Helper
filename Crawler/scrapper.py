
# scraper.py (simulado, ya importado)
from bs4 import BeautifulSoup
import requests

def scrape_page(url: str) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return {
        "title": soup.title.string if soup.title else "",
        "entities": [a.text for a in soup.find_all('a')][:5],
        "timestamp": response.headers.get("Date")
    }
