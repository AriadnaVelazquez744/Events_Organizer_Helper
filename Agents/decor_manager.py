# agents/decor_manager.py
from bs4 import BeautifulSoup
import requests
import re

from urllib.parse import quote_plus
from crawler.core.core import AdvancedCrawlerAgent
from typing import List, Dict, Any, Union, Optional
from crawler.extraction.expert import ExpertSystemInterface
from crawler.extraction.graph import KnowledgeGraphInterface
from Agents.decor_rag import DecorRAG

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
            r'\$(\d+(?:\.\d+)?)[^\d]*$',  # $XX o $XX.XX al final de la cadena
            r'(\d+(?:\.\d+)?)\s*(?:per item|each)',  # XX per item
            r'(\d+(?:\.\d+)?)\s*(?:total|minimum)',  # XX total
            r'(\d+(?:\.\d+)?)(?:\s*usd|\s*eur|\s*gbp|\s*mxn)?(?:\s*approx)?' # XX usd, XX eur, etc.
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
                    # print(f"[RULE] {data.get('title')} - campo '{campo}' ausente")
                    return False

                # Caso especial: Precio
                if campo == "price":
                    min_price = self._get_minimum_price(valor)
                    if min_price is None:
                        # print(f"[RULE] {data.get('title')} - precio no tiene valores numéricos válidos")
                        return False

                    if min_price <= valor_esperado:
                        return True

                    # print(f"[RULE] {data.get('title')} - precio mínimo {min_price} > presupuesto {valor_esperado}")
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

    def _calculate_bonus_score(self, data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score de bonificación basado en características especiales."""
        bonus_score = 0.0
        max_bonus = 0.0

        # Bonificación por servicios premium (2%)
        service_levels = data.get("service_levels", [])
        description = data.get("description", "").lower()
        if service_levels or description:
            max_bonus += 0.02
            premium_indicators = [
                "full-service", "luxury", "premium", "exclusive",
                "specialty", "unique", "high-end", "boutique"
            ]
            premium_count = 0
            # Buscar en niveles de servicio
            if service_levels:
                premium_count += sum(1 for service in service_levels if any(p in str(service).lower() for p in premium_indicators))
            # Buscar en descripción
            if description:
                premium_count += sum(1 for p in premium_indicators if p in description)
            bonus_score += min(premium_count / 5, 1.0) * 0.02

        # Bonificación por calidad y profesionalismo (2%)
        reviews = data.get("reviews", [])
        rating = data.get("rating", 0)
        if reviews or rating or description:
            max_bonus += 0.02
            quality_score = 0.0
            # Calcular score basado en rating
            if rating:
                quality_score += (rating / 5.0) * 0.01
            # Calcular score basado en número de reviews
            if reviews:
                quality_score += min(len(reviews) / 50, 1.0) * 0.01
            bonus_score += quality_score

        # Bonificación por variedad de servicios (2%)
        if service_levels:
            max_bonus += 0.02
            service_categories = {
                "pre_wedding": data.get("pre_wedding_services", []),
                "post_wedding": data.get("post_wedding_services", []),
                "day_of": data.get("day_of_services", []),
                "arrangements": data.get("floral_arrangements", []),
                "styles": data.get("arrangement_styles", [])
            }
            category_matches = 0
            for category, services in service_categories.items():
                if services and len(services) > 0:
                    category_matches += 1
            bonus_score += (category_matches / len(service_categories)) * 0.02

        # Bonificación por flexibilidad (2%)
        if description or service_levels:
            max_bonus += 0.02
            flexibility_indicators = [
                "custom", "flexible", "adaptable", "special requests",
                "personalized", "tailored", "modify", "change", "adjust"
            ]
            flex_count = 0
            # Buscar en servicios
            if service_levels:
                flex_count += sum(1 for service in service_levels if any(f in str(service).lower() for f in flexibility_indicators))
            # Buscar en descripción
            if description:
                flex_count += sum(1 for f in flexibility_indicators if f in description)
            bonus_score += min(flex_count / 5, 1.0) * 0.02

        # Bonificación por especialización (2%)
        styles = data.get("arrangement_styles", [])
        if description or styles:
            max_bonus += 0.02
            specialization_score = 0.0
            # Calcular score basado en número de estilos
            if styles:
                specialization_score += min(len(styles) / 5, 1.0) * 0.01
            # Calcular score basado en descripción
            if description:
                specialization_indicators = [
                    "specialized", "expert", "specialty", "specialist",
                    "focused", "dedicated", "professional", "experienced"
                ]
                spec_count = sum(1 for i in specialization_indicators if i in description)
                specialization_score += min(spec_count / 4, 1.0) * 0.01
            bonus_score += specialization_score

        #print(f" Score de bonificación para {data.get('title', 'Sin título')}: {bonus_score:.2f}")
        return bonus_score / max_bonus if max_bonus > 0 else 0.0

    def score_optional(self, knowledge: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score combinado de criterios opcionales e inferencias."""
        score = 0.0
        max_score = 0.0
        opcionales = criteria.get("opcionales", [])
        data = knowledge.get("original_data", knowledge)

        # Score de criterios opcionales (30% del total)
        for campo in opcionales:
            expected = criteria.get(campo)
            actual = data.get(campo)
            if expected is None or actual is None:
                continue

            max_score += 0.3
            if isinstance(expected, str) and isinstance(actual, str):
                if expected.lower() in actual.lower():
                    score += 0.3
            elif isinstance(expected, list):
                if isinstance(actual, list):
                    matched = set(e.lower() for e in expected) & set(a.lower() for a in actual)
                    score += (len(matched) / len(expected)) * 0.3
                elif isinstance(actual, str):
                    score += (sum(1 for e in expected if e.lower() in actual.lower()) / len(expected)) * 0.3
            elif actual == expected:
                score += 0.3

        # Score de inferencias (20% del total)
        inference_score = self._calculate_inference_score(data, criteria)
        score += inference_score * 0.2
        max_score += 0.2

        # Score de recomendaciones del RAG (40% del total)
        rag_score = 0.0
        rag_max_score = 0.0

        # Score de niveles de servicio recomendados (10%)
        if "service_levels" in criteria:
            rag_max_score += 0.10
            service_levels = data.get("service_levels", [])
            if service_levels:
                matched_services = set(s.lower() for s in service_levels) & set(s.lower() for s in criteria["service_levels"])
                service_score = len(matched_services) / len(criteria["service_levels"])
                rag_score += service_score * 0.10
                #print(f"[DecorAgent] Score de niveles de servicio: {len(matched_services)}/{len(criteria['service_levels'])} ({service_score:.2f})")

        # Score de servicios pre-boda recomendados (10%)
        if "pre_wedding_services" in criteria:
            rag_max_score += 0.10
            pre_services = data.get("pre_wedding_services", [])
            if pre_services:
                matched_pre = set(s.lower() for s in pre_services) & set(s.lower() for s in criteria["pre_wedding_services"])
                pre_score = len(matched_pre) / len(criteria["pre_wedding_services"])
                rag_score += pre_score * 0.10
                #print(f"[DecorAgent] Score de servicios pre-boda: {len(matched_pre)}/{len(criteria['pre_wedding_services'])} ({pre_score:.2f})")

        # Score de servicios post-boda recomendados (5%)
        if "post_wedding_services" in criteria:
            rag_max_score += 0.05
            post_services = data.get("post_wedding_services", [])
            if post_services:
                matched_post = set(s.lower() for s in post_services) & set(s.lower() for s in criteria["post_wedding_services"])
                post_score = len(matched_post) / len(criteria["post_wedding_services"])
                rag_score += post_score * 0.05
                #print(f"[DecorAgent] Score de servicios post-boda: {len(matched_post)}/{len(criteria['post_wedding_services'])} ({post_score:.2f})")

        # Score de servicios del día recomendados (5%)
        if "day_of_services" in criteria:
            rag_max_score += 0.05
            day_services = data.get("day_of_services", [])
            if day_services:
                matched_day = set(s.lower() for s in day_services) & set(s.lower() for s in criteria["day_of_services"])
                day_score = len(matched_day) / len(criteria["day_of_services"])
                rag_score += day_score * 0.05
                #print(f"[DecorAgent] Score de servicios del día: {len(matched_day)}/{len(criteria['day_of_services'])} ({day_score:.2f})")

        # Score de estilos de arreglo recomendados (5%)
        if "arrangement_styles" in criteria:
            rag_max_score += 0.05
            styles = data.get("arrangement_styles", [])
            if styles:
                matched_styles = set(s.lower() for s in styles) & set(s.lower() for s in criteria["arrangement_styles"])
                style_score = len(matched_styles) / len(criteria["arrangement_styles"])
                rag_score += style_score * 0.05
                #print(f"[DecorAgent] Score de estilos de arreglo: {len(matched_styles)}/{len(criteria['arrangement_styles'])} ({style_score:.2f})")

        # Score de arreglos florales recomendados (5%)
        if "floral_arrangements" in criteria:
            rag_max_score += 0.05
            arrangements = data.get("floral_arrangements", [])
            if arrangements:
                matched_arrangements = set(a.lower() for a in arrangements) & set(a.lower() for a in criteria["floral_arrangements"])
                arrangement_score = len(matched_arrangements) / len(criteria["floral_arrangements"])
                rag_score += arrangement_score * 0.05
                #print(f"[DecorAgent] Score de arreglos florales: {len(matched_arrangements)}/{len(criteria['floral_arrangements'])} ({arrangement_score:.2f})")

        # Normalizar score del RAG
        if rag_max_score > 0:
            score += (rag_score / rag_max_score) * 0.4
            max_score += 0.4

        # Score de bonificación por características especiales (10%)
        bonus_score = self._calculate_bonus_score(data, criteria)
        score += bonus_score * 0.1
        max_score += 0.1

        final_score = score / max_score if max_score > 0 else 0.0
        #print(f"[DecorAgent] Score final para {data.get('title', 'Sin título')}: {final_score:.2f}")
        return final_score

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
            print("[DecorAgent] Obteniendo recomendaciones del RAG...")
            decor_recommendation = self.rag.get_decor_recommendation(
                budget=criteria["budget"],
                guest_count=criteria["guest_count"],
                style=criteria.get("style", "classic")
            )
            
            # Actualizar criterios con las recomendaciones del RAG
            if decor_recommendation:
                print("[DecorAgent] Aplicando recomendaciones del RAG...")
                criteria["recommended_service_levels"] = decor_recommendation.get("service_levels", [])
                criteria["recommended_pre_wedding_services"] = decor_recommendation.get("pre_wedding_services", [])
                criteria["recommended_post_wedding_services"] = decor_recommendation.get("post_wedding_services", [])
                criteria["recommended_day_of_services"] = decor_recommendation.get("day_of_services", [])
                criteria["recommended_arrangement_styles"] = decor_recommendation.get("arrangement_styles", [])
                criteria["recommended_floral_arrangements"] = decor_recommendation.get("floral_arrangements", [])
                criteria["estimated_cost"] = decor_recommendation.get("estimated_cost", 0)
        else:
            print("[DecorAgent] No se encontraron campos necesarios para RAG (budget y guest_count)")

        # Verificar si ya tenemos datos en el grafo
        print("[DecorAgent] Verificando datos existentes en el grafo...")
        existing_data = self.graph.query("decor")
        if  len(existing_data) < 30:
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
                # print(f"[DecorAgent] Decorador válido: {data.get('title', 'Sin título')}")

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

    def receive(self, message: Dict[str, Any]):
        """Procesa mensajes entrantes."""
        if message["tipo"] == "task":
            task_id = message["contenido"]["task_id"]
            parameters = message["contenido"]["parameters"]
            session_id = message["session_id"]
            
            try:
                print(f"[DecorAgent] Procesando tarea de búsqueda de decoración")
                # Procesar la tarea
                results = self.find_decor(parameters, [])  # Por ahora lista vacía de URLs
                
                # Enviar respuesta
                return {
                    "origen": self.name,
                    "destino": message["origen"],
                    "tipo": "agent_response",
                    "contenido": {
                        "task_id": task_id,
                        "results": results
                    },
                    "session_id": session_id
                }
            except Exception as e:
                print(f"[DecorAgent] Error procesando tarea: {str(e)}")
                return {
                    "origen": self.name,
                    "destino": message["origen"],
                    "tipo": "error",
                    "contenido": {
                        "task_id": task_id,
                        "error": str(e)
                    },
                    "session_id": session_id
                }
        else:
            print(f"[DecorAgent] Tipo de mensaje no reconocido: {message['tipo']}")