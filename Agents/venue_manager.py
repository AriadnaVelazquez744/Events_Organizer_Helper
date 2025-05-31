
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

    def setup_rules(self, criteria: Dict[str, Any]):
        self.expert.clear_rules()
        obligatorios = criteria.get("obligatorios", [])

        for campo in obligatorios:
            valor_esperado = criteria.get(campo)

            def make_rule(campo, valor_esperado):
                def regla(knowledge):
                    data = knowledge.get("original_data", knowledge)
                    valor = data.get(campo)

                    if valor is None:
                        print(f"[RULE] {data.get('title')} - campo '{campo}' ausente")
                        return False

                    if isinstance(valor_esperado, (int, float)):
                        if isinstance(valor, dict):
                            # Busca en claves comunes
                            candidatos = []
                            for k in ['seated', 'standing', 'min', 'max']:
                                if isinstance(valor.get(k), (int, float)):
                                    candidatos.append(valor[k])
                            if not candidatos:
                                print(f"[RULE] {data.get('title')} - {campo} no tiene subcampos numéricos válidos")
                                return False
                            if max(candidatos) >= valor_esperado:
                                return True
                            print(f"[RULE] {data.get('title')} - {campo}={valor}, esperado ≥ {valor_esperado}")
                            return False
                        elif isinstance(valor, (int, float)):
                            if valor >= valor_esperado:
                                return True
                            print(f"[RULE] {data.get('title')} - {campo}={valor}, esperado ≥ {valor_esperado}")
                            return False
                        print(f"[RULE] {data.get('title')} - {campo} tiene formato inesperado: {valor}")
                        return False


                    elif isinstance(valor_esperado, str):
                        if valor_esperado.lower() not in str(valor).lower():
                            print(f"[RULE] {knowledge.get('title')} - {campo}='{valor}' no contiene '{valor_esperado}'")
                            return False
                        return True

                    elif isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            inter = set(v.lower() for v in valor) & set(e.lower() for e in valor_esperado)
                            if not inter:
                                print(f"[RULE] {knowledge.get('title')} - {campo} no tiene intersección con {valor_esperado}, actual: {valor}")
                                return False
                            return True
                        elif isinstance(valor, str):
                            if not any(e.lower() in valor.lower() for e in valor_esperado):
                                print(f"[RULE] {knowledge.get('title')} - {campo}='{valor}' no contiene elementos de {valor_esperado}")
                                return False
                            return True

                    else:
                        if valor != valor_esperado:
                            print(f"[RULE] {knowledge.get('title')} - {campo} = {valor} != {valor_esperado}")
                            return False
                        return True
                return regla


            self.expert.add_rule(make_rule(campo, valor_esperado))

    def score_optional(self, knowledge: Dict[str, Any], criteria: Dict[str, Any]) -> int:
        score = 0
        opcionales = criteria.get("opcionales", [])
        data = knowledge.get("original_data", knowledge)

        for campo in opcionales:
            expected = criteria.get(campo)
            actual = data.get(campo)
            if expected is None or actual is None:
                continue

            if isinstance(expected, str) and isinstance(actual, str):
                if expected.lower() in actual.lower():
                    score += 1
            elif isinstance(expected, list):
                if isinstance(actual, list):
                    matched = set(e.lower() for e in expected) & set(a.lower() for a in actual)
                    score += len(matched)
                elif isinstance(actual, str):
                    score += sum(1 for e in expected if e.lower() in actual.lower())
            elif actual == expected:
                score += 1

        return score

    def find_venues(self, criteria: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
        print("[VenueAgent] Crawling URLs...")
        self.setup_rules(criteria)
        # for url in urls:
        #     self.crawler.enqueue_url(url)

        # while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
        #     next_url = self.crawler.to_visit.pop(0)
        #     self.crawler.crawl(next_url, context=criteria)

        print("[VenueAgent] Procesando nodos tipo 'venue'...")
        candidates = self.graph.query("venue")

        valid = []
        for v in candidates:
            data = v.get("original_data", {})
            if self.expert.process_knowledge(data):
                valid.append((v, data))

        print(f"[VenueAgent] {len(valid)} venues válidos tras reglas obligatorias")

        scored = [(v[0], self.score_optional(v[1], criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [v for v, _ in scored]