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
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

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

def wait_for_element(driver, by, value, timeout=10):
    """Espera a que un elemento esté presente en la página."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except:
        return None

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
            
            # Espera inicial para carga de página
            time.sleep(5)
            
            # Para páginas de The Knot
            if "theknot.com" in url:
                # Espera a que el contenido principal esté cargado
                if "/marketplace/" in url and "?sort=featured" in url:
                    # Es una página de búsqueda
                    wait_for_element(driver, By.CLASS_NAME, "marketplace-search-results", timeout=15)
                else:
                    # Es una página de vendedor
                    wait_for_element(driver, By.CLASS_NAME, "vendor-profile", timeout=15)
                    # Scroll para cargar contenido dinámico
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
            
            html = driver.page_source
            with open("debug_last_scrape.html", "w", encoding="utf-8") as f:
                f.write(html)
            driver.quit()
        except Exception as e:
            print(f"[SCRAPER] Selenium falló: {e}")
            return {"url": url, "title": "ERROR", "outlinks": []}
    
    # Si es página de búsqueda
    if "/search/" in url or "?sort=featured" in url:
        outlinks = extract_venue_links(html)
        print("[SCRAPER] Links extraídos:", outlinks)
        return {
            "url": url,
            "title": "Search Page",
            "outlinks": outlinks,
            "tipo": "search"
        }

    # Inicializar structured con valores por defecto
    structured = {
        "url": url,
        "title": "Unknown",
        "ubication": None,
        "price": None,
        "service_levels": [],
        "pre_wedding_services": [],
        "post_wedding_services": [],
        "day_of_services": [],
        "arrangement_styles": [],
        "floral_arrangements": [],
        "restrictions": [],
        "outlinks": [],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # Determinar el tipo de página y usar el prompt correspondiente
    if "zola" in url and "wedding-venues" in url:
        result = llm_extract_openrouter(html, url=url, prompt_template=venue_prompt)
        if result:
            structured.update(result)
            structured["tipo"] = "venue"
    elif "zola" in url and "wedding-catering" in url:
        result = llm_extract_openrouter(html, url=url, prompt_template=catering_prompt)
        if result:
            structured.update(result)
            structured["tipo"] = "catering"
    elif "zola" in url and "wedding-florists" in url:
        result = llm_extract_openrouter(html, url=url, prompt_template=decor_prompt)
        if result:
            structured.update(result)
            structured["tipo"] = "decor"
    elif "theknot" in url:
        result = llm_extract_openrouter(html, url=url, prompt_template=decor_prompt)
        if result:
            structured.update(result)
            structured["tipo"] = "decor"

    # Extraer outlinks si no se han extraído antes
    if not structured.get("outlinks"):
        structured["outlinks"] = extract_venue_links(html)

    return structured

def extract_venue_links(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    venue_links = set()

    zola_venue_pattern = re.compile(r"^https://www\.zola\.com/wedding-vendors/wedding-venues/[a-z0-9\-]+/?$")
    zola_catering_pattern = re.compile(r"^https://www\.zola\.com/wedding-vendors/wedding-catering/[a-z0-9\-]+/?$")
    zola_florist_pattern = re.compile(r"^https://www\.zola\.com/wedding-vendors/wedding-florists/[a-z0-9\-]+/?$")
    knot_pattern = re.compile(r"^https://www\.theknot\.com/marketplace/[a-z0-9\-]+/?$")

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Normaliza URLs relativas
        if href.startswith("/wedding-vendors/wedding-venues/"):
            href = "https://www.zola.com" + href
        elif href.startswith("/wedding-vendors/wedding-catering/"):
            href = "https://www.zola.com" + href
        elif href.startswith("/wedding-vendors/wedding-florists/"):
            href = "https://www.zola.com" + href
        elif href.startswith("/marketplace/"):
            href = "https://www.theknot.com" + href

        if (
            zola_venue_pattern.match(href)
            or zola_catering_pattern.match(href)
            or zola_florist_pattern.match(href)
            or knot_pattern.match(href)
        ):
            venue_links.add(href)

    return list(venue_links)

venue_prompt = """
Extract event venue data from the following text if the text only mentions a venue:

- Venue name
- Capacity (number of people)
- Location
- Extract pricing information by splitting into:

- "space_rental": Fixed price for renting the venue (per event or per day), anything beginning with "starting at..."
- "per_person": Price per person, if applicable
- "other": Any additional prices mentioned

Returns a subJSON with this structure:

"price":
"space_rental": 3500,
"per_person": 41,
"other": [],

- Whether it's indoor, outdoor, or both (returns both values when it's both)
- Venue type (hotel, beach, farm, etc.)
- Included services
- Venue restrictions
- Supported event types
- URLs in the text that appear to correspond to other similar venues

If the text mentions multiple venues, it only searches and extracts URLs throughout the text even if they don't appear where a venue is mentioned.

Your response must be exactly a JSON with these exact keys, without any notes or reviews after, make shure that the json has a correct structure:
"title", "capacity", "location", "price", "atmosphere", "venue_type", "services", "restrictions", "supported_events", "outlinks"

Text:
{text}
"""

catering_prompt = """
Extracts data from the following text about a catering agency if the text only mentions one:

- Name
- Services
- Ubication
- Extracts pricing information

- Cuisines
- Dietary Options
- Meal types
- Beverage services
- Drink types
- Restrictions
- URLs in the text that appear to correspond to other similar locations

Your response must be exactly a JSON with these exact keys, without any notes or reviews after, make shure that the json has a correct structure:
"title", "services", "ubication", "price", "cuisines", "dietary_options", "meal_types", "beverage_services" , "drink_types" ,"restrictions", "outlinks"

Text:
{text}
"""

decor_prompt="""
    Extract data from the following text about a floral design service if the text only mentions one:

    - Name
    - Location
    - Price information
    - Service levels 
    - Pre-wedding services 
    - Post-wedding services 
    - Day-of services 
    - Arrangement styles 
    - Floral arrangements offered 
    - Restrictions
    - URLs in the text that appear to correspond to other similar services

    Your response must be exactly a JSON with these exact keys, without any notes or reviews after, make sure that the json has a correct structure:
    "title", "ubication", "price", "service_levels", "pre_wedding_services", "post_wedding_services", "day_of_services", "arrangement_styles", "floral_arrangements", "restrictions", "outlinks"

    Text:
    {text}
    """