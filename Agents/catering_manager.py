
# agents/venue_manager.py
from bs4 import BeautifulSoup
import requests

from urllib.parse import quote_plus
from Crawler.core import AdvancedCrawlerAgent
from typing import List, Dict, Any
from Crawler.expert import ExpertSystemInterface
from Crawler.graph import KnowledgeGraphInterface

class CateringAgent:
    def __init__(self, name: str, crawler: AdvancedCrawlerAgent, graph: KnowledgeGraphInterface, expert: ExpertSystemInterface):
        self.name = name
        self.crawler = crawler
        self.graph = graph
        self.expert = expert

    def setup_rules(self, criteria: Dict[str, Any]):
        self.expert.clear_rules()
        obligatorios = criteria.get("obligatorios", [])

        def make_rule(campo, valor_esperado):
        
            def regla(knowledge):
                data = knowledge.get("original_data", knowledge)
                valor = data.get(campo)

                if valor is None:
                    print(f"[RULE] {data.get('title')} - campo '{campo}' ausente")
                    return False

                # # 🚩 CASO ESPECIAL: CAPACIDAD
                # if campo == "capacidad":
                #     if isinstance(valor, dict):
                #         candidatos = [v for v in valor.values() if isinstance(v, (int, float))]
                #         if not candidatos:
                #             print(f"[RULE] {data.get('title')} - capacidad no tiene valores numéricos válidos")
                #             return False
                #         if max(candidatos) >= valor_esperado:
                #             return True
                #         print(f"[RULE] {data.get('title')} - capacidad={candidatos} < requerido {valor_esperado}")
                #         return False
                #     elif isinstance(valor, (int, float)):
                #         if valor >= valor_esperado:
                #             return True
                #         print(f"[RULE] {data.get('title')} - capacidad={valor} < requerido {valor_esperado}")
                #         return False
                #     return False

                # 🚩 CASO ESPECIAL: PRECIO
                elif campo == "precio":
                    if isinstance(valor, dict):
                        candidatos = [v for v in valor.values() if isinstance(v, (int, float)) and v > 0]
                        if not candidatos:
                            print(f"[RULE] {data.get('title')} - precio no tiene valores numéricos válidos")
                            return False
                        if any(p <= valor_esperado for p in candidatos):
                            return True
                        print(f"[RULE] {data.get('title')} - precio {candidatos} supera {valor_esperado}")
                        return False
                    elif isinstance(valor, (int, float)):
                        if valor <= valor_esperado:
                            return True
                        print(f"[RULE] {data.get('title')} - precio={valor} supera {valor_esperado}")
                        return False
                    return False

                # --- STRING ---
                elif isinstance(valor_esperado, str):
                    if valor_esperado.lower() not in str(valor).lower():
                        print(f"[RULE] {data.get('title')} - {campo}='{valor}' no contiene '{valor_esperado}'")
                        return False
                    return True

                # --- LISTA ---
                elif isinstance(valor_esperado, list):
                    if isinstance(valor, list):
                        inter = set(v.lower() for v in valor) & set(e.lower() for e in valor_esperado)
                        if not inter:
                            print(f"[RULE] {data.get('title')} - {campo} no tiene intersección con {valor_esperado}, actual: {valor}")
                            return False
                        return True
                    elif isinstance(valor, str):
                        if not any(e.lower() in valor.lower() for e in valor_esperado):
                            print(f"[RULE] {data.get('title')} - {campo}='{valor}' no contiene elementos de {valor_esperado}")
                            return False
                        return True

                # --- DEFAULT COMPARACIÓN DIRECTA ---
                else:
                    if valor != valor_esperado:
                        print(f"[RULE] {data.get('title')} - {campo} = {valor} != {valor_esperado}")
                        return False
                    return True

            return regla

        for campo in obligatorios:
            valor_esperado = criteria.get(campo)
            print(valor_esperado)
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

    def find_catering(self, criteria: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
        print("[CateringAgent] Crawling URLs...")
        self.setup_rules(criteria)
        for url in urls:
            self.crawler.enqueue_url(url)

        while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
            next_url = self.crawler.to_visit.pop(0)
            self.crawler.crawl(next_url, context=criteria)

        print("[CateringAgent] Procesando nodos tipo 'catering'...")
        candidates = self.graph.query("catering")

        valid = []
        for v in candidates:
            data = v.get("original_data", {})
            if self.expert.process_knowledge(data):
                valid.append((v, data))

        print(f"[cateringAgent] {len(valid)} caterings válidos tras reglas obligatorias")

        scored = [(v[0], self.score_optional(v[1], criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        return [v for v, _ in scored]