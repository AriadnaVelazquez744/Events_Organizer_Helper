# crawler/core.py (actualizado)
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

            knowledge = self.extract_knowledge(content, url, context)
            print(f"[CRAWLER] Extrajo conocimiento: {knowledge}")
            self.graph_interface.insert_knowledge(knowledge)

            if self.expert_system:
                self.expert_system.process_knowledge(knowledge)

            self._log("SUCCESS", f"Procesado: {url}")

            # Expansión
            if depth > 0:
                for next_url in content.get("outlinks", []):
                    self.crawl(next_url, context=context, depth=depth - 1)

        except Exception as e:
            self._log("ERROR", f"{url} falló: {str(e)}")


    def extract_knowledge(self, content: Dict[str, Any], url: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": url,
            "title": content.get("title", "").strip(),
            "entities": content.get("entities", []),
            "capacidad": content.get("capacidad"),
            "tipo": "venue",
            "precio": content.get("precio"),
            "ciudad": content.get("ciudad"),
            "tipo_evento": content.get("tipo_evento"),
            "timestamp": content.get("timestamp", datetime.utcnow().isoformat())
        }

    def _log(self, level: str, message: str):
        log_entry = f"[{self.name}] [{level}] {datetime.utcnow().isoformat()} - {message}"
        print(log_entry)
        self.log.append(log_entry)