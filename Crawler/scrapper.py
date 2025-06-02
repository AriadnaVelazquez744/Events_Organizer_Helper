
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
            time.sleep(3)  # espera para carga dinámica
            html = driver.page_source
            with open("debug_last_scrape.html", "w", encoding="utf-8") as f:
                f.write(html)
            driver.quit()
        except Exception as e:
            print(f"[SCRAPER] Selenium falló: {e}")
            return {"url": url, "title": "ERROR", "outlinks": []}
    
    # Si es página de búsqueda
    if "/search/" in url or "sort=featured" in url:
        outlinks = extract_venue_links(html)
        print("[SCRAPER] Links extraídos:", outlinks)
        return {
            "url": url,
            "title": "Search Page",
            "outlinks": outlinks,
            "tipo": "search"
        }
    venue_prompt = """
Extrae del siguiente texto los datos de un lugar para eventos si el texto solo menciona un lugar:

- Nombre del lugar
- Capacidad (número de personas)
- Ubicación
- Extrae la información de precios dividiendo en:

- "alquiler_espacio": precio fijo por alquilar el lugar (por evento o por día), cualquier cosa que empiece por "starting at ..."
- "por_persona": precio por persona, si aplica
- "otros": cualquier precio adicional mencionado

Incluye también notas o condiciones especiales (por ejemplo, si es solo para ciertas fechas).

Devuelve un subJSON con esta estructura:

  "precio": 
    "alquiler_espacio": 3500,
    "por_persona": 41,
    "otros": [],
    "notas": "..."
  

- Si es interior, exterior o ambos(cuando sea ambos devuelve los dos valores )
- Tipo de local (hotel, playa, granja, etc.)
- Servicios incluidos
- Restricciones del lugar
- Tipos de eventos compatibles
- URLs en el texto que parezcan corresponder a otros lugares similares

Si el texto menciona varios lugares solo busca y extrae URLs en todo el texto aunque no aparezcan donde se menciona un lugar

Devuelve un JSON con estas claves exactas:
"title", "capacidad", "ubicación", "precio", "ambiente", "tipo_local", "servicios", "restricciones", "eventos_compatibles", "outlinks"


Texto:
{text}
"""

    catering_prompt = venue_prompt = """
Extrae del siguiente texto los datos de una agencia de catering si el texto solo menciona una:

- Nombre 
- Area de Servicio
- Extrae la información de precios

- Cuisine
- Dietary Options
- Catering
- Restricciones
- URLs en el texto que parezcan corresponder a otros lugares similares

Devuelve un JSON con estas claves exactas:
"title", "service area", "precio", "cuisine", "dietary_options", "catering", "outlinks"


Texto:
{text}
"""

    structured = llm_extract_openrouter(html, url=url, prompt_template=venue_prompt)
    structured["url"] = url
    structured["tipo"] = "venue"
    structured["outlinks"] = extract_venue_links(html)
    structured["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return structured

def extract_venue_links(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    venue_links = set()

    zola_pattern = re.compile(r"^https://www\.zola\.com/wedding-vendors/wedding-venues/[a-z0-9\-]+/?$")
    knot_pattern = re.compile(r"^https://www\.theknot\.com/marketplace/[a-z0-9\-]+/?$")

    for a in soup.find_all("a", href=True):
        href = a["href"]

        if href.startswith("/wedding-vendors/wedding-venues/"):
            href = "https://www.zola.com" + href
        elif href.startswith("/marketplace/"):
            href = "https://www.theknot.com" + href

        if zola_pattern.match(href) or knot_pattern.match(href):
            venue_links.add(href)

    return list(venue_links)