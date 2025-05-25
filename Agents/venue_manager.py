
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
            if isinstance(capacidad, dict):  # en caso de estructura avanzada
                capacidad_val = capacidad.get("sentados") or capacidad.get("de_pie")
            else:
                capacidad_val = capacidad

            if min_capacidad is not None and capacidad_val < min_capacidad:
                print(f"[RULE] Descarta {knowledge.get('title')} por baja capacidad")
                return False
            return True

        def rule_presupuesto(knowledge):
            precio = knowledge.get("precio")
            max_presupuesto = criteria.get("presupuesto")
            if precio is None or max_presupuesto is None:
                print(f"[RULE] Descarta {knowledge.get('title')} por precio ausente o sin criterio")
                return False

            if isinstance(precio, dict):
                precios_numericos = [v for k, v in precio.items() if isinstance(v, (int, float))]
                if not precios_numericos:
                    print(f"[RULE] {knowledge.get('title')} sin precios comparables")
                    return False
                if all(p > max_presupuesto for p in precios_numericos):
                    print(f"[RULE] Descarta {knowledge.get('title')} por sobrepresupuesto")
                    return False
            elif isinstance(precio, (int, float)):
                if precio > max_presupuesto:
                    print(f"[RULE] Descarta {knowledge.get('title')} por sobrepresupuesto")
                    return False
            else:
                print(f"[RULE] {knowledge.get('title')} con precio no procesable")
                return False
            return True

        # def rule_ciudad(knowledge):
        #     ciudad = knowledge.get("ciudad")
        #     criterio_ciudad = criteria.get("ciudad")
        #     if ciudad is None:
        #         print(f"[RULE] Descarta {knowledge.get('title')} por ciudad ausente")
        #         return False
        #     if criterio_ciudad and criterio_ciudad.lower() not in ciudad.lower():
        #         print(f"[RULE] Descarta {knowledge.get('title')} por ciudad no coincidente")
        #         return False
        #     return True

        self.expert.clear_rules()
        self.expert.add_rule(rule_capacity)
        self.expert.add_rule(rule_presupuesto)
        # self.expert.add_rule(rule_ciudad)



    def find_venues(self, criteria, urls):
        print(1)
        self.setup_rules(criteria)
        for url in urls:
            self.crawler.crawl(url, context=criteria, depth=1)  # profundidad de expansión
        return self.graph.query("venue")

    