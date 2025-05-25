# crawler/core.py (actualizado)
from urllib.parse import urlparse
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
        self.max_visits = 50

    def crawl(self, url: str, context: Dict[str, Any] = None, depth: int = 1):
        print(2)
        if url in self.visited:
            print(f"[CRAWLER] Ya visitado: {url}")
            return

        # Solo registrar el bloqueo, pero no abortar
        if not self.policy.can_fetch(url):
            print(f"[CRAWLER] Robots.txt bloquea: {url} (continuando con Selenium si es necesario)")

        if len(self.visited) >= self.max_visits:
            print(f"[CRAWLER] Límite de {self.max_visits} URLs alcanzado.")
            return

        self.policy.wait()
        self.visited.add(url)

        try:
            print(f"[CRAWLER] Scrapeando: {url}")
            content = scrape_page(url, context)
            print(f"[CRAWLER] Contenido scrapeado: {bool(content)}")

            content.setdefault("url", url)
            content.setdefault("tipo", "venue")
            content.setdefault("timestamp", datetime.utcnow().isoformat())
            knowledge = content
            print(f"[CRAWLER] Extrajo conocimiento: {knowledge}")
            self.graph_interface.insert_knowledge(knowledge)

            if self.expert_system:
                self.expert_system.process_knowledge(knowledge)

            self._log("SUCCESS", f"Procesado: {url}")

            if depth > 0:
                base_domain = urlparse(url).netloc
                outlinks = content.get("outbound_links") or content.get("outlinks") or []
                for next_url in outlinks:
                    if isinstance(next_url, str) and next_url.startswith("http"):
                        # opcional: limitar al mismo dominio
                        if urlparse(next_url).netloc == base_domain:
                            self.crawl(next_url, context=context, depth=depth - 1)

        except Exception as e:
            self._log("ERROR", f"{url} falló: {str(e)}")



    def _log(self, level: str, message: str):
        log_entry = f"[{self.name}] [{level}] {datetime.utcnow().isoformat()} - {message}"
        print(log_entry)
        self.log.append(log_entry)