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

    def crawl(self, url: str, context: Dict[str, Any] = None):
        if not self.policy.can_fetch(url):
            self._log("BLOCKED", f"robots.txt bloquea: {url}")
            return

        self.policy.wait()
        try:
            content = scrape_page(url, context)
            knowledge = self.extract_knowledge(content, url, context)
            self.graph_interface.insert_knowledge(knowledge)

            if self.expert_system:
                self.expert_system.process_knowledge(knowledge)

            self._log("SUCCESS", f"Procesado: {url}")
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