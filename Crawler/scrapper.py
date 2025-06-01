
# scraper.py
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import re
from Crawler.llm_extract_openrouter import llm_extract_openrouter

def setup_driver():
    options = Options()
    # QUITA el modo headless
    # options.add_argument("--headless")  # Desactivado
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("start-maximized")
    options.add_argument("window-size=1920x1080")

    # User-Agent falso
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
    )

    return driver


def scrape_page(url: str, context: dict = None) -> dict:
    html = None
    print(f"[SCRAPER] Intentando requests: {url}")
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200 and len(response.text.strip()) > 1000:
            html = response.text
    except Exception as e:
        print(f"[SCRAPER] Requests falló: {e}")

    if not html:
        print("[SCRAPER] Usando Selenium con scroll y espera...")
        try:
            driver = setup_driver()
            driver.get(url)

            # Espera opcional: espera a que cargue una clase común
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/wedding-vendors/wedding-venues/']"))
                )
            except:
                print("[SCRAPER] Advertencia: No se detectó selector esperado, usando scroll de todas formas")

            # Scroll para cargar contenido dinámico
            for _ in range(4):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

            html = driver.page_source

            # DEBUG: guarda el HTML para inspección manual
            with open("debug_output.html", "w", encoding="utf-8") as f:
                f.write(html)

            driver.quit()

        except Exception as e:
            print(f"[SCRAPER] Selenium falló: {e}")
            return {"url": url, "title": "ERROR", "outlinks": []}

    if "/search/" in url or "theknot.com/marketplace" in url:
        outlinks = extract_venue_links(html)
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
    structured["outlinks"] = extract_venue_links(html)
    structured["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return structured


def extract_venue_links(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    venue_links = set()

    # Zola
    zola_pattern = re.compile(r"^https://www\.zola\.com/wedding-vendors/wedding-venues/[a-z0-9\-]+/?$")
    # The Knot
    knot_pattern = re.compile(r"^https://www\.theknot\.com/marketplace/[\w\-]+-wedding-venues-[\w\-]+/?$")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("/wedding-vendors/wedding-venues/"):
            href = "https://www.zola.com" + href
        if href.startswith("/marketplace/"):
            href = "https://www.theknot.com" + href

        if zola_pattern.match(href) or knot_pattern.match(href):
            venue_links.add(href)

    return list(venue_links)
