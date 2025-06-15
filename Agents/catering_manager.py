# agents/venue_manager.py
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import quote_plus
from Crawler.core import AdvancedCrawlerAgent
from typing import List, Dict, Any, Union, Optional
from Crawler.expert import ExpertSystemInterface
from Crawler.graph import KnowledgeGraphInterface
from catering_rag import CateringRAG

class CateringAgent:
    def __init__(self, name: str, crawler: AdvancedCrawlerAgent, graph: KnowledgeGraphInterface, expert: ExpertSystemInterface):
        self.name = name
        self.crawler = crawler
        self.graph = graph
        self.expert = expert
        self.inference_rules = {}
        self.rag = CateringRAG()  # Inicializa el sistema RAG

    def _extract_price_value(self, price_str: str) -> Optional[float]:
        """Extrae el valor numérico de un string de precio."""
        if isinstance(price_str, (int, float)):
            return float(price_str)
        
        # Busca patrones como "$XX", "XX per person", etc.
        patterns = [
            r'\$(\d+(?:\.\d+)?)',  # $XX o $XX.XX
            r'(\d+(?:\.\d+)?)\s*(?:per person|pp|each)',  # XX per person
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

    def _calculate_inference_score(self, data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score basado en inferencias sobre los datos."""
        score = 0.0
        max_score = 0.0

        # Inferencia de calidad basada en servicios
        services = data.get("services", [])
        if services:
            max_score += 1.0
            if isinstance(services, list):
                if len(services) >= 5:  # Más servicios sugiere mejor calidad
                    score += 1.0
                elif len(services) >= 3:
                    score += 0.5

        # Inferencia de flexibilidad basada en opciones dietéticas
        dietary = data.get("dietary_options", [])
        if dietary:
            max_score += 1.0
            if isinstance(dietary, list):
                if len(dietary) >= 5:  # Más opciones dietéticas sugiere más flexibilidad
                    score += 1.0
                elif len(dietary) >= 3:
                    score += 0.5

        # Inferencia de variedad basada en tipos de comida
        cuisines = data.get("cuisines", [])
        if cuisines:
            max_score += 1.0
            if isinstance(cuisines, list):
                if len(cuisines) >= 8:  # Más tipos de comida sugiere más variedad
                    score += 1.0
                elif len(cuisines) >= 4:
                    score += 0.5

        # Inferencia de profesionalismo basada en servicios de bebidas
        beverage_services = data.get("beverage_services", [])
        if beverage_services:
            max_score += 1.0
            if isinstance(beverage_services, list):
                if "Provides liquor license" in beverage_services:
                    score += 1.0
                elif len(beverage_services) >= 3:
                    score += 0.5
            elif isinstance(beverage_services, str):
                if "liquor license" in beverage_services.lower():
                    score += 1.0
                elif len(beverage_services.split()) >= 3:
                    score += 0.5

        return score / max_score if max_score > 0 else 0.0

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

                # Caso especial: Ubicación
                elif campo == "ubication":
                    if isinstance(valor, list):
                        return any(valor_esperado.lower() in loc.lower() for loc in valor)
                    return valor_esperado.lower() in str(valor).lower()

                # Caso especial: Servicios
                elif campo == "services":
                    if isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            return any(s.lower() in [v.lower() for v in valor] for s in valor_esperado)
                        return any(s.lower() in str(valor).lower() for s in valor_esperado)
                    return valor_esperado.lower() in str(valor).lower()

                # Caso especial: Opciones dietéticas
                elif campo == "dietary_options":
                    if isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            # Convertir todo a minúsculas para comparación
                            valor_lower = [v.lower() for v in valor]
                            valor_esperado_lower = [v.lower() for v in valor_esperado]
                            return all(d in valor_lower for d in valor_esperado_lower)
                        return all(d.lower() in str(valor).lower() for d in valor_esperado)
                    return valor_esperado.lower() in str(valor).lower()

                # Caso especial: Tipos de comida
                elif campo == "meal_types":
                    if isinstance(valor_esperado, list):
                        if isinstance(valor, list):
                            # Mapeo de tipos de comida equivalentes
                            meal_type_mapping = {
                                "plated": ["seated meal", "plated"],
                                "buffet": ["buffet"]
                            }
                            
                            # Convertir todo a minúsculas para comparación
                            valor_lower = [v.lower() for v in valor]
                            valor_esperado_lower = [v.lower() for v in valor_esperado]
                            
                            # Verificar cada tipo de comida esperado
                            for meal_type in valor_esperado_lower:
                                if meal_type in meal_type_mapping:
                                    if not any(equivalent in valor_lower for equivalent in meal_type_mapping[meal_type]):
                                        print(f"[RULE] {data.get('title')} - no tiene {meal_type} o equivalente")
                                    return False
                                elif meal_type not in valor_lower:
                                    print(f"[RULE] {data.get('title')} - no tiene {meal_type}")
                            return False
                        return True
                        return all(d.lower() in str(valor).lower() for d in valor_esperado)
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

    def find_catering(self, criteria: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
        print("[CateringAgent] Iniciando búsqueda de catering...")
        self.setup_rules(criteria)

        # Obtener recomendaciones del RAG
        if "budget" in criteria and "guest_count" in criteria:
            menu_recommendation = self.rag.get_menu_recommendation(
                budget=criteria["budget"],
                guest_count=criteria["guest_count"],
                dietary_requirements=criteria.get("dietary_options", ["regular"]),
                style=criteria.get("style", "standard")
            )
            
            # Actualizar criterios con las recomendaciones del RAG
            if menu_recommendation:
                criteria["recommended_courses"] = menu_recommendation["courses"]
                criteria["recommended_dietary_options"] = menu_recommendation["dietary_options"]
                criteria["estimated_cost"] = menu_recommendation["estimated_cost"]
                
                # Si hay restricciones dietéticas, obtener alternativas
                if "dietary_options" in criteria:
                    alternatives = self.rag.suggest_dietary_alternatives(criteria["dietary_options"])
                    criteria["dietary_alternatives"] = alternatives

        # Verificar si ya tenemos datos en el grafo
        print("[CateringAgent] Verificando datos existentes en el grafo...")
        existing_data = self.graph.query("catering")
        if not existing_data:
            print("[CateringAgent] No hay datos en el grafo, iniciando crawling...")
            for url in urls:
                self.crawler.enqueue_url(url)

            while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
                next_url = self.crawler.to_visit.pop(0)
                self.crawler.crawl(next_url, context=criteria)
        else:
            print(f"[CateringAgent] Se encontraron {len(existing_data)} caterings en el grafo")

        print("[CateringAgent] Procesando nodos tipo 'catering'...")
        candidates = self.graph.query("catering")
        print(f"[CateringAgent] Se encontraron {len(candidates)} candidatos iniciales")

        valid = []
        for v in candidates:
            data = v.get("original_data", {})
            if not data:
                print(f"[CateringAgent] Advertencia: Nodo sin datos originales: {v.get('nombre', 'Desconocido')}")
                continue
                
            if self.expert.process_knowledge(data):
                valid.append((v, data))
                print(f"[CateringAgent] Catering válido: {data.get('title', 'Sin título')}")

        print(f"[CateringAgent] {len(valid)} caterings válidos tras reglas obligatorias")

        if not valid:
            print("[CateringAgent] Advertencia: No se encontraron caterings válidos")
            print("[CateringAgent] Criterios aplicados:", criteria)
            return []

        scored = [(v[0], self.score_optional(v[1], criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Limitar a los 50 mejores resultados
        results = [v for v, _ in scored[:50]]
        
        # Actualizar patrones de éxito en RAG
        if results:
            self.rag.update_success_pattern(
                {
                    "style": criteria.get("style", "standard"),
                    "courses": criteria.get("recommended_courses", []),
                    "dietary_options": criteria.get("dietary_options", ["regular"]),
                    "estimated_cost": criteria.get("estimated_cost", 0),
                    "guest_count": criteria.get("guest_count", 0)
                },
                True  # Asumimos éxito si encontramos resultados
            )
        
        print(f"[CateringAgent] Se retornan los {len(results)} mejores resultados")
        return results