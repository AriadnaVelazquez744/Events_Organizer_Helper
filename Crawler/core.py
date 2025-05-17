# crawler/core.py (actualizado)
from typing import Dict, Any
from scrapper import scrape_page
from policy import CrawlPolicy

class CrawlerAgent:
    def __init__(self, name: str, graph_interface, expert_system=None, policy=None):
        self.name = name
        self.graph_interface = graph_interface
        self.expert_system = expert_system
        self.policy = policy or CrawlPolicy()

    def crawl(self, url: str):
        if not self.policy.can_fetch(url):
            print(f"[BLOCKED] Robots.txt does not allow: {url}")
            return

        self.policy.wait()
        content = scrape_page(url)
        knowledge = self.extract_knowledge(content, url)
        self.graph_interface.insert_knowledge(knowledge)

        if self.expert_system:
            self.expert_system.process_knowledge(knowledge)

    def extract_knowledge(self, content: Dict[str, Any], url: str) -> Dict[str, Any]:
        entities = [e for e in content.get("entities", []) if e.strip()]
        return {
            "url": url,
            "title": content.get("title", "").strip(),
            "entities": entities,
            "timestamp": content.get("timestamp")
        }
