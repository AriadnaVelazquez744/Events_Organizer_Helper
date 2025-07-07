# agents/venue_manager.py
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import quote_plus
from src.crawler.core.core import AdvancedCrawlerAgent
from typing import List, Dict, Any, Union, Optional
from src.crawler.extraction.expert import ExpertSystemInterface
from src.crawler.extraction.graph import KnowledgeGraphInterface
from src.agents.catering.catering_rag import CateringRAG
import json

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

    def _calculate_bonus_score(self, data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score de bonificación basado en características especiales."""
        bonus_score = 0.0
        max_bonus = 0.0

        # Bonificación por servicios premium (2%)
        # Inferimos servicios premium de la descripción y servicios existentes
        services = data.get("services", [])
        description = data.get("description", "").lower()
        if services or description:
            max_bonus += 0.02
            premium_indicators = [
                "chef", "wine", "mixology", "live cooking", "dessert bar",
                "specialty", "gourmet", "premium", "exclusive", "signature"
            ]
            premium_count = 0
            # Buscar en servicios
            if services:
                premium_count += sum(1 for service in services if any(p in str(service).lower() for p in premium_indicators))
            # Buscar en descripción
            if description:
                premium_count += sum(1 for p in premium_indicators if p in description)
            bonus_score += min(premium_count / 5, 1.0) * 0.02

        # Bonificación por calidad y profesionalismo (2%)
        # Inferimos de reviews, ratings y descripción
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
        # Inferimos de la cantidad y diversidad de servicios
        if services:
            max_bonus += 0.02
            service_categories = {
                "food": ["catering", "menu", "food", "dinner", "lunch", "breakfast"],
                "beverage": ["bar", "drinks", "wine", "cocktail", "beverage"],
                "service": ["staff", "service", "waiting", "setup", "cleanup"],
                "equipment": ["rental", "equipment", "tables", "chairs", "linens"],
                "special": ["custom", "special", "unique", "theme", "event"]
            }
            category_matches = 0
            for category, keywords in service_categories.items():
                if any(k in str(services).lower() for k in keywords):
                    category_matches += 1
            bonus_score += (category_matches / len(service_categories)) * 0.02

        # Bonificación por flexibilidad (2%)
        # Inferimos de la descripción y servicios
        if description or services:
            max_bonus += 0.02
            flexibility_indicators = [
                "custom", "flexible", "adaptable", "special requests",
                "personalized", "tailored", "modify", "change", "adjust"
            ]
            flex_count = 0
            # Buscar en servicios
            if services:
                flex_count += sum(1 for service in services if any(f in str(service).lower() for f in flexibility_indicators))
            # Buscar en descripción
            if description:
                flex_count += sum(1 for f in flexibility_indicators if f in description)
            bonus_score += min(flex_count / 5, 1.0) * 0.02

        # Bonificación por especialización (2%)
        # Inferimos de la descripción y tipos de comida
        cuisines = data.get("cuisines", [])
        if description or cuisines:
            max_bonus += 0.02
            specialization_score = 0.0
            # Calcular score basado en número de tipos de comida
            if cuisines:
                specialization_score += min(len(cuisines) / 5, 1.0) * 0.01
            # Calcular score basado en descripción
            if description:
                specialization_indicators = [
                    "specialized", "expert", "specialty", "specialist",
                    "focused", "dedicated", "professional", "experienced"
                ]
                spec_count = sum(1 for i in specialization_indicators if i in description)
                specialization_score += min(spec_count / 4, 1.0) * 0.01
            bonus_score += specialization_score

        #print(f"[CateringAgent] Score de bonificación para {data.get('title', 'Sin título')}: {bonus_score:.2f}")
        return bonus_score / max_bonus if max_bonus > 0 else 0.0

    def setup_rules(self, criteria: Dict[str, Any]):
        """Configura las reglas de validación basadas en los criterios."""
        self.expert.clear_rules()
        obligatorios = criteria.get("obligatorios", [])

        def make_rule(campo, valor_esperado):
            def regla(knowledge):
                data = knowledge.get("original_data", knowledge)
                valor = data.get(campo)

                if valor is None:
                    # print(f"[RULE] {data.get('title')} - campo '{campo}' ausente")
                    return False

                # 🚩 CASO ESPECIAL: PRECIO
                if campo == "price":
                    min_price = self._get_minimum_price(valor)
                    if min_price is None:
                        # print(f"[RULE] {data.get('title')} - precio no tiene valores numéricos válidos")
                        return False

                    if min_price <= valor_esperado:
                            return True

                    # print(f"[RULE] {data.get('title')} - precio mínimo {min_price} > presupuesto {valor_esperado}")
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

                # # Caso especial: Tipos de comida
                # elif campo == "meal_types":
                #     if isinstance(valor_esperado, list):
                #         if isinstance(valor, list):
                #             # Mapeo de tipos de comida equivalentes
                #             meal_type_mapping = {
                #                 "plated": ["seated meal", "plated"],
                #                 "buffet": ["buffet"]
                #             }
                            
                #             # Convertir todo a minúsculas para comparación
                #             valor_lower = [v.lower() for v in valor]
                #             valor_esperado_lower = [v.lower() for v in valor_esperado]
                            
                #             # Verificar cada tipo de comida esperado
                #             for meal_type in valor_esperado_lower:
                #                 if meal_type in meal_type_mapping:
                                   
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
                                    # Si el tipo está en el mapeo, verificar sus equivalentes
                                    if not any(equivalent in valor_lower for equivalent in meal_type_mapping[meal_type]):
                                        # print(f"[RULE] {data.get('title')} - no tiene {meal_type} o equivalente")
                                        return False
                                elif meal_type not in valor_lower:
                                    # Si el tipo no está en el mapeo, verificar directamente
                                    # print(f"[RULE] {data.get('title')} - no tiene {meal_type}")
                                    return False
                            return True
                        else:
                            # Si valor no es una lista, verificar si contiene todos los tipos esperados
                            valor_str = str(valor).lower()
                            return all(d.lower() in valor_str for d in valor_esperado)
                    else:
                        # Si valor_esperado no es una lista, verificar coincidencia directa
                        return valor_esperado.lower() in str(valor).lower()

                # --- DEFAULT COMPARACIÓN DIRECTA ---
                else:
                    if valor != valor_esperado:
                        # print(f"[RULE] {data.get('title')} - {campo} = {valor} != {valor_esperado}")
                        return False
                    return True

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

        # Score de cursos recomendados (15%)
        if "recommended_courses" in criteria:
            rag_max_score += 0.15
            courses = data.get("courses", [])
            if courses:
                matched_courses = set(c.lower() for c in courses) & set(c.lower() for c in criteria["recommended_courses"])
                course_score = len(matched_courses) / len(criteria["recommended_courses"])
                rag_score += course_score * 0.15
                #print(f"[CateringAgent] Score de cursos recomendados: {len(matched_courses)}/{len(criteria['recommended_courses'])} ({course_score:.2f})")

        # Score de opciones dietéticas (15%)
        if "recommended_dietary_options" in criteria:
            rag_max_score += 0.15
            dietary = data.get("dietary_options", [])
            if dietary:
                matched_dietary = set(d.lower() for d in dietary) & set(d.lower() for d in criteria["recommended_dietary_options"])
                dietary_score = len(matched_dietary) / len(criteria["recommended_dietary_options"])
                rag_score += dietary_score * 0.15
                #print(f" de opciones dietéticas: {len(matched_dietary)}/{len(criteria['recommended_dietary_options'])} ({dietary_score:.2f})")

        # Score de alternativas dietéticas (10%)
        if "dietary_alternatives" in criteria:
            rag_max_score += 0.10
            dietary = data.get("dietary_options", [])
            alternatives_score = 0.0
            if dietary:
                for restriction, alternatives in criteria["dietary_alternatives"].items():
                    if restriction.lower() in [d.lower() for d in dietary]:
                        alternatives_score += 0.5
                    if any(alt.lower() in [d.lower() for d in dietary] for alt in alternatives["alternatives"]):
                        alternatives_score += 0.5
                rag_score += (alternatives_score / len(criteria["dietary_alternatives"])) * 0.10
                #print(f"[CateringAgent] Score de alternativas dietéticas: {alternatives_score:.2f}")

        # Normalizar score del RAG
        if rag_max_score > 0:
            score += (rag_score / rag_max_score) * 0.4
            max_score += 0.4

        # Score de bonificación por características especiales (10%)
        bonus_score = self._calculate_bonus_score(data, criteria)
        score += bonus_score * 0.1
        max_score += 0.1

        final_score = score / max_score if max_score > 0 else 0.0
        #print(f"[CateringAgent] Score final para {data.get('title', 'Sin título')}: {final_score:.2f}")
        return final_score

    def find_catering(self, criteria: Dict[str, Any], urls: List[str]) -> List[Dict[str, Any]]:
        print("[CateringAgent] Iniciando búsqueda de catering...")
        self.setup_rules(criteria)

        # Obtener recomendaciones del RAG
        if "budget" in criteria and "guest_count" in criteria:
            print("[CateringAgent] Obteniendo recomendaciones del RAG...")
            print(f"[CateringAgent] Criterios para RAG: budget={criteria['budget']}, guest_count={criteria['guest_count']}")
            menu_recommendation = self.rag.get_menu_recommendation(
                budget=criteria["budget"],
                guest_count=criteria["guest_count"],
                dietary_requirements=criteria.get("dietary_options", ["regular"]),
                style=criteria.get("style", "standard")
            )
            
            # Actualizar criterios con las recomendaciones del RAG
            if menu_recommendation:
                print("[CateringAgent] Aplicando recomendaciones del RAG...")
                print(f"[CateringAgent] Recomendaciones del RAG: {json.dumps(menu_recommendation, indent=2)}")
                criteria["recommended_courses"] = menu_recommendation["courses"]
                criteria["recommended_dietary_options"] = menu_recommendation["dietary_options"]
                criteria["estimated_cost"] = menu_recommendation["estimated_cost"]
                
                # Si hay restricciones dietéticas, obtener alternativas
                if "dietary_options" in criteria:
                    alternatives = self.rag.suggest_dietary_alternatives(criteria["dietary_options"])
                    print(f"[CateringAgent] Alternativas dietéticas sugeridas: {json.dumps(alternatives, indent=2)}")
                    criteria["dietary_alternatives"] = alternatives
            else:
                print("[CateringAgent] ⚠️ No se obtuvieron recomendaciones del RAG")
        else:
            print("[CateringAgent] No se encontraron campos necesarios para RAG (budget y guest_count)")
            print(f"[CateringAgent] Criterios disponibles: {json.dumps(criteria, indent=2)}")

        # Verificar si ya tenemos datos en el grafo
        print("[CateringAgent] Verificando datos existentes en el grafo...")
        existing_data = self.graph.query("catering")
        if  len(existing_data) < 60:
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
                # print(f"[t] Catering válido: {data.get('title', 'Sin título')}")

        print(f"[CateringAgent] {len(valid)} caterings válidos tras reglas obligatorias")

        if not valid:
            print("[CateringAgent] Advertencia: No se encontraron caterings válidos")
            print("[CateringAgent] Criterios aplicados:", criteria)
            # --- NUEVO: Búsqueda web automática si no hay resultados válidos ---
            print("[CateringAgent] Lanzando búsqueda web automática...")
            try:
                from duckduckgo_search import DDGS
                # --- Construcción de la query con todos los campos obligatorios ---
                obligatorios = criteria.get('obligatorios', [])
                query_parts = []
                for campo in obligatorios:
                    valor = criteria.get(campo)
                    if valor is None:
                        continue
                    # Formateo natural para algunos campos
                    if campo == 'guest_count':
                        query_parts.append(f"{valor} guests")
                    elif campo == 'price':
                        query_parts.append(f"${valor}")
                    else:
                        if isinstance(valor, list):
                            query_parts.extend([str(v) for v in valor])
                        else:
                            query_parts.append(str(valor))
                query_base = "wedding catering " + " ".join(query_parts)
                subqueries = [
                    f"site:zola.com {query_base}",
                    f"site:theknot.com {query_base}",
                    f"{query_base} zola",
                    f"{query_base} theknot"
                ]
                relaxed_query = query_base
                web_urls = []
                for subq in subqueries:
                    print(f"[CateringAgent] Query enviada a DuckDuckGo: {subq}")
                    with DDGS() as ddgs:
                        search_results = list(ddgs.text(subq, max_results=15))
                    urls = [r['href'] for r in search_results if 'href' in r]
                    print(f"[CateringAgent] Resultados encontrados: {len(urls)}")
                    web_urls.extend(urls)
                if not web_urls:
                    print(f"[CateringAgent] Query enviada a DuckDuckGo (relajada): {relaxed_query}")
                    with DDGS() as ddgs:
                        search_results = list(ddgs.text(relaxed_query, max_results=15))
                    urls = [r['href'] for r in search_results if 'href' in r]
                    print(f"[CateringAgent] Resultados encontrados (relajada): {len(urls)}")
                    web_urls.extend(urls)
                if not web_urls:
                    print('[CateringAgent] No se encontraron URLs relevantes. No se hará crawling.')
                    return []
                print(f"[CateringAgent] URLs encontradas en la web: {web_urls}")
                for url in web_urls:
                    self.crawler.enqueue_url(url)
                while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
                    next_url = self.crawler.to_visit.pop(0)
                    if not self.crawler.policy.can_fetch(next_url):
                        print(f"[CateringAgent] robots.txt bloquea: {next_url}. No se hará crawling.")
                        continue
                    self.crawler.crawl(next_url, context=criteria)
                print("[CateringAgent] Guardando grafo después del crawling web...")
                self.graph.save_to_file("catering_graph.json")
                self.graph.clean_errors()
                candidates = self.graph.query("catering")
                print(f"[CateringAgent] Nodos tipo 'catering' encontrados después del crawling web: {len(candidates)}")
                valid = []
                for v in candidates:
                    data = v.get("original_data", {})
                    if not data:
                        continue
                    if self.expert.process_knowledge(data):
                        valid.append((v, data))
                print(f"[CateringAgent] {len(valid)} caterings válidos tras búsqueda web")
                if not valid:
                    print("[CateringAgent] No se encontraron caterings válidos ni tras búsqueda web")
                    return []
            except Exception as e:
                print(f"[CateringAgent] Error en búsqueda web automática: {e}")
                return []

        scored = [(v[0], self.score_optional(v[1], criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Limitar a los 50 mejores resultados
        results = [v for v, _ in scored[:50]]
        
        # Actualizar patrones de éxito en RAG
        if results:
            print("[CateringAgent] Actualizando patrones de éxito en RAG...")
            pattern_data = {
                "style": criteria.get("style", "standard"),
                "courses": criteria.get("recommended_courses", []),
                "dietary_options": criteria.get("dietary_options", ["regular"]),
                "estimated_cost": criteria.get("estimated_cost", 0),
                "guest_count": criteria.get("guest_count", 0)
            }
            print(f"[CateringAgent] Datos del patrón a actualizar: {json.dumps(pattern_data, indent=2)}")
            self.rag.update_success_pattern(pattern_data, True)
            print("[CateringAgent] Patrón de éxito actualizado")
        
        print(f"[CateringAgent] Se retornan los {len(results)} mejores resultados")
        return results

    def receive(self, message: Dict[str, Any]):
        """Procesa mensajes entrantes."""
        if message["tipo"] == "task":
            task_id = message["contenido"]["task_id"]
            parameters = message["contenido"]["parameters"]
            session_id = message["session_id"]
            
            try:
                print(f"[CateringAgent] Procesando tarea de búsqueda de catering")
                # Procesar la tarea
                results = self.find_catering(parameters, [])  # Por ahora lista vacía de URLs
                
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
                print(f"[CateringAgent] Error procesando tarea: {str(e)}")
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
            print(f"[CateringAgent] Tipo de mensaje no reconocido: {message['tipo']}")