
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

    structured = llm_extract_openrouter(html, url=url)
    print(structured)
    structured["url"] = url
    structured["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return structured