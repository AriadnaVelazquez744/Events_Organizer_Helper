
# scraper.py
import re
from bs4 import BeautifulSoup
import requests
import time
from Crawler.llm_extract_openrouter import llm_extract_openrouter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scrape_page(url: str, context: dict = None) -> dict:
    html = None
    print(f"[SCRAPER] Intentando requests: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            html = response.text
        else:
            print(f"[SCRAPER] Código no 200: {response.status_code}")
    except Exception as e:
        print(f"[SCRAPER] Requests falló: {e}")

    if not html or len(html.strip()) < 1000:
        print("[SCRAPER] Usando Selenium...")
        try:
            driver = setup_driver()
            driver.get(url)
        #    time.sleep(3)
            html = driver.page_source
            driver.quit()
        except Exception as e:
            print(f"[SCRAPER] Selenium falló: {e}")
            return {"url": url, "title": "ERROR", "outlinks": []}
        
    if "/search/" in url:
        outlinks = extract_zola_venue_links(html)
        print("[SCRAPER] Links extraídos:", outlinks)
        return {
            "url": url,
            "title": "Search Page",
            "outlinks": outlinks,
            "tipo": "search"
        }
        
    structured = llm_extract_openrouter(html, url=url)
    structured["url"] = url
    structured["tipo"] = "venue"
    structured["outlinks"] = extract_zola_venue_links(html)  # por si hay más venues referenciados
    structured["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return structured
    

def extract_zola_venue_links(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    venue_links = set()

    # Patrón para URLs válidas de venues en Zola
    pattern = re.compile(r"^https://www\.zola\.com/wedding-vendors/wedding-venues/[a-z0-9\-]+/?$")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Normalizar a URL absoluta si es relativa
        if href.startswith("/wedding-vendors/wedding-venues/"):
            href = "https://www.zola.com" + href
        if pattern.match(href):
            venue_links.add(href)

    return list(venue_links)