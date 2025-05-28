
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
        self.expert.clear_rules()
        obligatorios = criteria.get("obligatorios", [])

        for campo in obligatorios:
            valor_esperado = criteria.get(campo)

            def make_rule(campo, valor_esperado):
                def regla(knowledge):
                    valor = knowledge.get(campo)
                    if valor is None:
                        print(f"[RULE] Descarta por {campo} ausente")
                        return False

                    # Regla para numérico
                    if isinstance(valor_esperado, (int, float)):
                        if isinstance(valor, dict):  # ej: precio
                            numericos = [v for v in valor.values() if isinstance(v, (int, float))]
                            if any(v <= valor_esperado for v in numericos):
                                return True
                            print(f"[RULE] Descarta por {campo} > esperado")
                            return False
                        elif isinstance(valor, (int, float)):
                            if valor <= valor_esperado:
                                return True
                            print(f"[RULE] Descarta por {campo} > esperado")
                            return False
                        return False

                    # Regla para string
                    elif isinstance(valor_esperado, str):
                        return valor_esperado.lower() in str(valor).lower()

                    # Regla para lista
                    elif isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            inter = set([v.lower() for v in valor]) & set([e.lower() for e in valor_esperado])
                            return bool(inter)
                        elif isinstance(valor, str):
                            return any(e.lower() in valor.lower() for e in valor_esperado)

                    # Fallback
                    return valor == valor_esperado
                return regla

            self.expert.add_rule(make_rule(campo, valor_esperado))

    def score_optional(self, venue, criteria):
        score = 0
        opcionales = criteria.get("opcionales", [])

        for campo in opcionales:
            expected = criteria.get(campo)
            real = venue.get(campo)
            if expected is None or real is None:
                continue

            if isinstance(real, str) and isinstance(expected, str):
                if expected.lower() in real.lower():
                    score += 1
            elif isinstance(real, list):
                matched = [item for item in real if item.lower() in expected.lower()] if isinstance(expected, str) else set(real) & set(expected)
                score += len(matched)
            elif real == expected:
                score += 1

        return score

    def find_venues(self, criteria, urls):
        print("[VenueAgent] Crawling URLs...")
        self.setup_rules(criteria)
        for url in urls:
            self.crawler.enqueue_url(url)
            
        while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
            next_url = self.crawler.to_visit.pop(0)
            self.crawler.crawl(next_url, context=criteria)

        candidates = self.graph.query("venue")
        print(f"[VenueAgent] {len(candidates)} venues en grafo")

        valid = [v for v in candidates if self.expert.process_knowledge(v)]
        print(f"[VenueAgent] {len(valid)} venues válidos tras reglas obligatorias")

        scored = [(v, self.score_optional(v, criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [v for v, _ in scored]



    # def find_venues(self, criteria, urls):
    #     print("[VENUE AGENT] Iniciando búsqueda de venues")
    #     self.setup_rules(criteria)
    #     for url in urls:
    #         self.crawler.enqueue_url(url)

    #     while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
    #         next_url = self.crawler.to_visit.pop(0)
    #         self.crawler.crawl(next_url, context=criteria)
        
    #     return self.graph.query("venue")

    