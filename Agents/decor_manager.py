# agents/decor_manager.py
from bs4 import BeautifulSoup
import requests
import re

from urllib.parse import quote_plus
from Crawler.core import AdvancedCrawlerAgent
from typing import List, Dict, Any, Union, Optional
from Crawler.expert import ExpertSystemInterface
from Crawler.graph import KnowledgeGraphInterface
from decor_rag import DecorRAG

class DecorAgent:
    def __init__(self, name: str, crawler: AdvancedCrawlerAgent, graph: KnowledgeGraphInterface, expert: ExpertSystemInterface):
        self.name = name
        self.crawler = crawler
        self.graph = graph
        self.expert = expert
        self.rag = DecorRAG()  # Inicializa el sistema RAG

    def _extract_price_value(self, price_str: str) -> Optional[float]:
        """Extrae el valor numérico de un string de precio."""
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        # Busca patrones como "$XX", "XX per item", etc.
        patterns = [
            r'\$(\d+(?:\.\d+)?)',  # $XX o $XX.XX
            r'(\d+(?:\.\d+)?)\s*(?:per item|each)',  # XX per item
            r'(\d+(?:\.\d+)?)\s*(?:total|minimum)',  # XX total
        ]
        
        for pattern in patterns:
            match = re.search(pattern, str(price_str).lower())
            if match:
                return float(match.group(1))
        return None

    def _get_minimum_price(self, price_data: Union[Dict, List, str, int, float]) -> Optional[float]:
        """Obtiene el precio mínimo de cualquier estructura de precio."""
        if isinstance(price_data, (int, float)):
            return float(price_data)
        
        if isinstance(price_data, str):
            return self._extract_price_value(price_data)
        
        if isinstance(price_data, list):
            prices = []
            for item in price_data:
                if isinstance(item, (int, float)):
                    prices.append(float(item))
                elif isinstance(item, str):
                    val = self._extract_price_value(item)
                    if val is not None:
                        prices.append(val)
            return min(prices) if prices else None
        
        if isinstance(price_data, dict):
            prices = []
            for key, value in price_data.items():
                if isinstance(value, (int, float)):
                    prices.append(float(value))
                elif isinstance(value, str):
                    val = self._extract_price_value(value)
                    if val is not None:
                        prices.append(val)
                elif isinstance(value, dict):
                    sub_price = self._get_minimum_price(value)
                    if sub_price is not None:
                        prices.append(sub_price)
            return min(prices) if prices else None
        
        return None

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

                # Caso especial: Precio
                if campo == "price":
                    min_price = self._get_minimum_price(valor)
                    if min_price is None:
                        print(f"[RULE] {data.get('title')} - precio no tiene valores numéricos válidos")
                        return False

                    if min_price <= valor_esperado:
                        return True

                    print(f"[RULE] {data.get('title')} - precio mínimo {min_price} > presupuesto {valor_esperado}")
                    return False

                # Caso especial: Niveles de servicio
                elif campo == "service_levels":
                    if isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            return any(s.lower() in [v.lower() for v in valor] for s in valor_esperado)
                        return any(s.lower() in str(valor).lower() for s in valor_esperado)
                    return valor_esperado.lower() in str(valor).lower()

                # Caso especial: Arreglos florales
                elif campo == "floral_arrangements":
                    if isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            return any(a.lower() in [v.lower() for v in valor] for a in valor_esperado)
                        return any(a.lower() in str(valor).lower() for a in valor_esperado)
                    return valor_esperado.lower() in str(valor).lower()

                # Caso especial: Estilos de arreglo
                elif campo == "arrangement_styles":
                    if isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            return any(s.lower() in [v.lower() for v in valor] for s in valor_esperado)
                        return any(s.lower() in str(valor).lower() for s in valor_esperado)
                    return valor_esperado.lower() in str(valor).lower()

                # Caso por defecto: comparación directa
                else:
                    if isinstance(valor_esperado, str):
                        return valor_esperado.lower() in str(valor).lower()
                    return valor == valor_esperado

            return regla

        for campo in obligatorios:
            valor_esperado = criteria.get(campo)
            if valor_esperado is not None:
                self.expert.add_rule(make_rule(campo, valor_esperado))

    def score_optional(self, knowledge: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score combinado de criterios opcionales e inferencias."""
        score = 0.0
        max_score = 0.0
        opcionales = criteria.get("opcionales", [])
        data = knowledge.get("original_data", knowledge)

        # Score de criterios opcionales
        for campo in opcionales:
            expected = criteria.get(campo)
            actual = data.get(campo)
            if expected is None or actual is None:
                continue

            max_score += 1.0
            if isinstance(expected, str) and isinstance(actual, str):
                if expected.lower() in actual.lower():
                    score += 1.0
            elif isinstance(expected, list):
                if isinstance(actual, list):
                    matched = set(e.lower() for e in expected) & set(a.lower() for a in actual)
                    score += len(matched) / len(expected)
                elif isinstance(actual, str):
                    score += sum(1 for e in expected if e.lower() in actual.lower()) / len(expected)
            elif actual == expected:
                score += 1.0

        # Score de inferencias
        inference_score = self._calculate_inference_score(data, criteria)
        score += inference_score
        max_score += 1.0

        return score / max_score if max_score > 0 else 0.0

    def _calculate_inference_score(self, data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score basado en inferencias sobre los datos."""
        score = 0.0
        max_score = 0.0

        # Inferencia de calidad basada en servicios pre-boda
        pre_wedding = data.get("pre_wedding_services", [])
        if pre_wedding:
            max_score += 1.0
            if isinstance(pre_wedding, list):
                if len(pre_wedding) >= 4:  # Más servicios pre-boda sugiere mejor calidad
                    score += 1.0
                elif len(pre_wedding) >= 2:
                    score += 0.5

        # Inferencia de variedad basada en arreglos florales
        arrangements = data.get("floral_arrangements", [])
        if arrangements:
            max_score += 1.0
            if isinstance(arrangements, list):
                if len(arrangements) >= 8:  # Más tipos de arreglos sugiere más variedad
                    score += 1.0
                elif len(arrangements) >= 4:
                    score += 0.5

        # Inferencia de flexibilidad basada en servicios del día
        day_services = data.get("day_of_services", [])
        if day_services:
            max_score += 1.0
            if isinstance(day_services, list):
                if len(day_services) >= 4:  # Más servicios del día sugiere más flexibilidad
                    score += 1.0
                elif len(day_services) >= 2:
                    score += 0.5

        # Inferencia de especialización basada en estilos
        styles = data.get("arrangement_styles", [])
        if styles:
            max_score += 1.0
            if isinstance(styles, list):
                if len(styles) >= 3:  # Más estilos sugiere más especialización
                    score += 1.0
                elif len(styles) >= 2:
                    score += 0.5

        return score / max_score if max_score > 0 else 0.0

    def find_decor(self, criteria: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
        print("[DecorAgent] Iniciando búsqueda de decoración...")
        self.setup_rules(criteria)

        # Obtener recomendaciones del RAG
        if "budget" in criteria and "guest_count" in criteria:
            decor_recommendation = self.rag.get_decor_recommendation(
                budget=criteria["budget"],
                guest_count=criteria["guest_count"],
                style=criteria.get("style", "classic")
            )
            
            # Actualizar criterios con las recomendaciones del RAG
            if decor_recommendation:
                criteria["recommended_decorations"] = decor_recommendation["decorations"]
                criteria["recommended_paper_goods"] = decor_recommendation["paper_goods"]
                criteria["recommended_rentals"] = decor_recommendation["rentals"]
                criteria["estimated_cost"] = decor_recommendation["estimated_cost"]

        # Verificar si ya tenemos datos en el grafo
        print("[DecorAgent] Verificando datos existentes en el grafo...")
        existing_data = self.graph.query("decor")
        if not existing_data:
            print("[DecorAgent] No hay datos en el grafo, iniciando crawling...")
            for url in urls:
                self.crawler.enqueue_url(url)

            while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
                next_url = self.crawler.to_visit.pop(0)
                self.crawler.crawl(next_url, context=criteria)
        else:
            print(f"[DecorAgent] Se encontraron {len(existing_data)} decoradores en el grafo")

        print("[DecorAgent] Procesando nodos tipo 'decor'...")
        candidates = self.graph.query("decor")
        print(f"[DecorAgent] Se encontraron {len(candidates)} candidatos iniciales")

        valid = []
        for v in candidates:
            data = v.get("original_data", {})
            if not data:
                print(f"[DecorAgent] Advertencia: Nodo sin datos originales: {v.get('nombre', 'Desconocido')}")
                continue
                
            if self.expert.process_knowledge(data):
                valid.append((v, data))
                print(f"[DecorAgent] Decorador válido: {data.get('title', 'Sin título')}")

        print(f"[DecorAgent] {len(valid)} decoradores válidos tras reglas obligatorias")

        if not valid:
            print("[DecorAgent] Advertencia: No se encontraron decoradores válidos")
            print("[DecorAgent] Criterios aplicados:", criteria)
            return []

        scored = [(v[0], self.score_optional(v[1], criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Limitar a los 50 mejores resultados
        results = [v for v, _ in scored[:50]]
        
        # Actualizar patrones de éxito en RAG
        if results:
            self.rag.update_success_pattern(
                {
                    "style": criteria.get("style", "classic"),
                    "decorations": criteria.get("recommended_decorations", []),
                    "paper_goods": criteria.get("recommended_paper_goods", []),
                    "rentals": criteria.get("recommended_rentals", []),
                    "estimated_cost": criteria.get("estimated_cost", 0),
                    "guest_count": criteria.get("guest_count", 0)
                },
                True  # Asumimos éxito si encontramos resultados
            )
        
        print(f"[DecorAgent] Se retornan los {len(results)} mejores resultados")
        return results