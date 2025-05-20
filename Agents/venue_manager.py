
# agents/venue_manager.py
from bs4 import BeautifulSoup
import requests

from urllib.parse import quote_plus
from Crawler.core import AdvancedCrawlerAgent
from typing import List, Dict, Any
from Crawler.expert import ExpertSystemInterface
from Crawler.graph import KnowledgeGraphInterface

class VenueAgent:
    def __init__(self, name: str, crawler: AdvancedCrawlerAgent, graph: KnowledgeGraphInterface, expert: ExpertSystemInterface):
        self.name = name
        self.crawler = crawler
        self.graph = graph
        self.expert = expert
        
    def setup_rules(self, criteria):
        def rule_capacity(knowledge):
            capacidad = knowledge.get("capacidad")
            min_capacidad = criteria.get("capacidad")
            if capacidad is None:
                print(f"[RULE] Descarta {knowledge.get('title')} por capacidad ausente")
                return False
            if min_capacidad is not None and capacidad < min_capacidad:
                print(f"[RULE] Descarta {knowledge.get('title')} por baja capacidad")
                return False
            return True

        def rule_presupuesto(knowledge):
            precio = knowledge.get("precio")
            max_precio = criteria.get("presupuesto")
            if precio is None:
                print(f"[RULE] Descarta {knowledge.get('title')} por precio ausente")
                return False
            if max_precio is not None and precio > max_precio:
                print(f"[RULE] Descarta {knowledge.get('title')} por sobrepresupuesto")
                return False
            return True

        def rule_ciudad(knowledge):
            ciudad = knowledge.get("ciudad")
            criterio_ciudad = criteria.get("ciudad")
            if ciudad is None:
                print(f"[RULE] Descarta {knowledge.get('title')} por ciudad ausente")
                return False
            if criterio_ciudad and criterio_ciudad.lower() not in ciudad.lower():
                print(f"[RULE] Descarta {knowledge.get('title')} por ciudad no coincidente")
                return False
            return True

        self.expert.add_rule(rule_capacity)
        self.expert.add_rule(rule_presupuesto)
        self.expert.add_rule(rule_ciudad)


    def find_venues(self, criteria, urls):
        self.setup_rules(criteria)
        for url in urls:
            self.crawler.crawl(url, context=criteria)
        return self.graph.query("venue")
        return results

    