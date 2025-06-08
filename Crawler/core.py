# crawler/core.py (actualizado)
import re
from urllib.parse import urlparse, urljoin
from typing import Callable, List, Dict, Any
from Crawler.scrapper import scrape_page
from Crawler.policy import CrawlPolicy
from datetime import datetime

class AdvancedCrawlerAgent:
    
    def __init__(self, name: str, graph_interface, expert_system=None, policy=None, mission_profile=None):
        self.name = name
        self.graph_interface = graph_interface
        self.expert_system = expert_system
        self.policy = policy or CrawlPolicy()
        self.mission_profile = mission_profile or {}
        self.log = []
        self.visited = set()
        self.max_visits = 6
        self.to_visit = []  # nueva pila FIFO

    def enqueue_url(self, url):
        if "search" in url and "?page=" in url:
            self.to_visit.append(url)
        else:    
            if (
                url in self.visited 
                or url in self.to_visit 
                or url in self.graph_interface.nodes
            ):
                print(f"[CRAWLER] Ignorando URL ya conocida: {url}")
                return
            self.to_visit.append(url)



    def crawl(self, url: str, context: Dict[str, Any] = None, depth: int = 0):
        print("[CRAWLER] Iniciando scrape de:", url)

        if url in self.visited:
            print(f"[CRAWLER] Ya visitado: {url}")
            return

        if not self.policy.can_fetch(url):
            print(f"[CRAWLER] Robots.txt bloquea: {url} (continuando con Selenium si es necesario)")

        if len(self.visited) >= self.max_visits:
            print(f"[CRAWLER] Límite de {self.max_visits} URLs alcanzado.")
            return

        self.policy.wait()
        self.visited.add(url)

        try:
            content = scrape_page(url, context)
            print(f"[CRAWLER] Contenido scrapeado: {bool(content)}")

            # Asegura campos mínimos
            content.setdefault("url", url)
            content.setdefault("tipo", "venue")
            content.setdefault("timestamp", datetime.utcnow().isoformat())
            knowledge = content

            # Insertar en el grafo
            self.graph_interface.insert_knowledge(knowledge)

            # Evaluar con el sistema experto
            if self.expert_system:
                self.expert_system.process_knowledge(knowledge)

            self._log("SUCCESS", f"Procesado: {url}")

            # === EXPANSIÓN DE URLS ===
            outlinks = content.get("outbound_links") or content.get("outlinks") or []
            base_domain = urlparse(url).netloc

            # 1. Agregar outlinks relevantes
            for next_url in outlinks:
                if isinstance(next_url, str) and next_url.startswith("http"):
                    if urlparse(next_url).netloc == base_domain:
                        self.enqueue_url(next_url)

            # 2. Si es página de búsqueda, intentar paginar
            if "search" in url and "?page=" in url:
                match = re.search(r"\?page=(\d+)", url)
                if match:
                    current_page = int(match.group(1))
                    next_page_url = re.sub(r"\?page=\d+", f"?page={current_page + 1}", url)
                    self.enqueue_url(next_page_url)
            elif "search" in url and "?page=" not in url:
                self.enqueue_url(url + "?page=2")

        except Exception as e:
            self._log("ERROR", f"{url} falló: {str(e)}")



    def _log(self, level: str, message: str):
        log_entry = f"[{self.name}] [{level}] {datetime.utcnow().isoformat()} - {message}"
        print(log_entry)
        self.log.append(log_entry)