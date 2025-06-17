# agents/venue_manager.py
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import quote_plus
from Crawler.core import AdvancedCrawlerAgent
from typing import List, Dict, Any, Union, Optional
from Crawler.expert import ExpertSystemInterface
from Crawler.graph import KnowledgeGraphInterface
from Agents.venue_rag import VenueRAG
import json

class VenueAgent:
    def __init__(self, name: str, crawler: AdvancedCrawlerAgent, graph: KnowledgeGraphInterface, expert: ExpertSystemInterface):
        self.name = name
        self.crawler = crawler
        self.graph = graph
        self.expert = expert
        # Pesos para el scoring
        self.WEIGHTS = {
            'base_score': 0.6,  # Reducido de 0.7
            'compatibility': 0.2,  # Reducido de 0.3
            'bonus': 0.2  # Nuevo factor
        }
        self.rag = VenueRAG()  # Inicializa el sistema RAG

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

                # 🚩 CASO ESPECIAL: CAPACIDAD
                if campo == "capacity":
                    if isinstance(valor, dict):
                        candidatos = [v for v in valor.values() if isinstance(v, (int, float))]
                        if not candidatos:
                            # print(f"[RULE] {data.get('title')} - capacidad no tiene valores numéricos válidos")
                            return False
                        if max(candidatos) >= valor_esperado:
                            return True
                        # print(f"[RULE] {data.get('title')} - capacidad={candidatos} < requerido {valor_esperado}")
                        return False
                    elif isinstance(valor, (int, float)):
                        if valor >= valor_esperado:
                            return True
                        # print(f"[RULE] {data.get('title')} - capacidad={valor} < requerido {valor_esperado}")
                        return False
                    return False

                # 🚩 CASO ESPECIAL: PRECIO
                elif campo == "price":
                    if isinstance(valor, dict):
                        candidatos = []
                        for k, v in valor.items():
                            if isinstance(v, (int, float)) and v > 0:
                                candidatos.append(v)
                            elif isinstance(v, dict):
                                for subv in v.values():
                                    if isinstance(subv, (int, float)) and subv > 0:
                                        candidatos.append(subv)
                            elif isinstance(v, list):
                                for item in v:
                                    if isinstance(item, dict):
                                        for subv in item.values():
                                            if isinstance(subv, (int, float)) and subv > 0:
                                                candidatos.append(subv)
                                    elif isinstance(item, (int, float)) and item > 0:
                                        candidatos.append(item)

                        if not candidatos:
                            # print(f"[RULE] {data.get('title')} - precio no tiene valores numéricos válidos")
                            return False

                        precio_max = max(candidatos)
                        if precio_max <= valor_esperado:
                            return True

                        # print(f"[RULE] {data.get('title')} - precio máximo {precio_max} > presupuesto {valor_esperado}")
                        return False

                    elif isinstance(valor, (int, float)):
                        if valor <= valor_esperado:
                            return True
                        print(f" {data.get('title')} - precio={valor} > {valor_esperado}")
                        return False

                    # print(f"[RULE] {data.get('title')} - precio con formato inesperado: {valor}")
                    return False

                # --- STRING ---
                elif isinstance(valor_esperado, str):
                    if valor_esperado.lower() not in str(valor).lower():
                        # print(f"[RULE] {data.get('title')} - {campo}='{valor}' no contiene '{valor_esperado}'")
                        return False
                    return True

                # --- LISTA ---
                elif isinstance(valor_esperado, list):
                    if isinstance(valor, list):
                        inter = set(v.lower() for v in valor) & set(e.lower() for e in valor_esperado)
                        if not inter:
                            print(f" {data.get('title')} - {campo} no tiene intersección con {valor_esperado}, actual: {valor}")
                            return False
                        return True
                    elif isinstance(valor, str):
                        if not any(e.lower() in valor.lower() for e in valor_esperado):
                            # print(f"[RULE] {data.get('title')} - {campo}='{valor}' no contiene elementos de {valor_esperado}")
                            return False
                        return True

                # --- DEFAULT COMPARACIÓN DIRECTA ---
                else:
                    if valor != valor_esperado:
                        # print(f"[RULE] {data.get('title')} - {campo} = {valor} != {valor_esperado}")
                        return False
                    return True

            return regla

        for campo in obligatorios:
            valor_esperado = criteria.get(campo)
            if valor_esperado is not None:  # Solo agregar regla si hay un valor esperado
                print(f"[VenueAgent] Agregando regla para {campo} con valor esperado: {valor_esperado}")
                self.expert.add_rule(make_rule(campo, valor_esperado))
            else:
                print(f"[VenueAgent] Advertencia: No se encontró valor esperado para {campo}")

    def get_related_venues(self, venue_id: str, max_distance: int = 1) -> List[Dict[str, Any]]:
        """Obtiene venues relacionados a través de relaciones en el grafo"""
        related = set()
        to_visit = [(venue_id, 0)]  # (node_id, distance)
        visited = set()

        while to_visit and len(related) < 10:  # Limitar a 10 venues relacionados
            current_id, distance = to_visit.pop(0)
            if current_id in visited or distance > max_distance:
                continue

            visited.add(current_id)
            current_node = self.graph.nodes.get(current_id)
            if not current_node:
                continue

            # Añadir nodos relacionados
            for from_id, rel, to_id in self.graph.edges:
                if from_id == current_id and to_id not in visited:
                    to_visit.append((to_id, distance + 1))
                    if self.graph.nodes[to_id].get("tipo") == "venue":
                        related.add(to_id)
                elif to_id == current_id and from_id not in visited:
                    to_visit.append((from_id, distance + 1))
                    if self.graph.nodes[from_id].get("tipo") == "venue":
                        related.add(from_id)

        return [self.graph.nodes[vid] for vid in related]

    def calculate_compatibility_score(self, venue1: Dict[str, Any], venue2: Dict[str, Any]) -> float:
        """Calcula un score de compatibilidad entre dos venues"""
        score = 0.0
        data1 = venue1.get("original_data", venue1)
        data2 = venue2.get("original_data", venue2)

        # Comparar tipos de venue
        if data1.get("venue_type") and data2.get("venue_type"):
            if isinstance(data1["venue_type"], list) and isinstance(data2["venue_type"], list):
                common_types = set(t.lower() for t in data1["venue_type"]) & set(t.lower() for t in data2["venue_type"])
                score += len(common_types) * 0.2

        # Comparar servicios
        if data1.get("services") and data2.get("services"):
            if isinstance(data1["services"], list) and isinstance(data2["services"], list):
                common_services = set(s.lower() for s in data1["services"]) & set(s.lower() for s in data2["services"])
                score += len(common_services) * 0.1

        # Comparar eventos soportados
        if data1.get("supported_events") and data2.get("supported_events"):
            if isinstance(data1["supported_events"], list) and isinstance(data2["supported_events"], list):
                common_events = set(e.lower() for e in data1["supported_events"]) & set(e.lower() for e in data2["supported_events"])
                score += len(common_events) * 0.15

        # Comparar ambiente
        if data1.get("atmosphere") and data2.get("atmosphere"):
            if isinstance(data1["atmosphere"], list) and isinstance(data2["atmosphere"], list):
                common_atmosphere = set(a.lower() for a in data1["atmosphere"]) & set(a.lower() for a in data2["atmosphere"])
                score += len(common_atmosphere) * 0.25

        return min(score, 1.0)

    def calculate_bonus_score(self, data: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Calcula un score de bonus basado en características especiales"""
        bonus = 0.0
        
        # Bonus por capacidad óptima (no muy grande ni muy pequeña)
        if data.get("capacity") is not None:
            capacity = data["capacity"]
            target_capacity = criteria.get("capacity", 0)
            if max(capacity, target_capacity) > 0:
                ratio = min(capacity, target_capacity) / max(capacity, target_capacity)
                bonus += ratio * 0.2

        # Bonus por precio óptimo (más bajo que el máximo)
        if data.get("price") is not None:
            price = data["price"]
            max_price = criteria.get("price", float('inf'))
            if isinstance(price, dict):
                space_rental = price.get("space_rental")
                if space_rental is not None:
                    if isinstance(space_rental, dict):
                        # Ensure space_rental values are not empty or all zero before max
                        numeric_values = [v for v in space_rental.values() if isinstance(v, (int, float)) and v > 0]
                        if numeric_values:
                            space_rental = max(numeric_values)
                        else:
                            space_rental = 0 # If no valid numeric values, treat as 0

                    if isinstance(space_rental, (int, float)) and space_rental >= 0 and max_price > 0:
                        ratio = 1 - (space_rental / max_price)
                        bonus += ratio * 0.2
            elif isinstance(price, (int, float)) and price >= 0 and max_price > 0: # Handle non-dict price values
                ratio = 1 - (price / max_price)
                bonus += ratio * 0.2

        # Bonus por servicios adicionales
        if data.get("services"):
            services = data["services"]
            if isinstance(services, list):
                premium_services = {"catering", "bar", "dance floor", "dressing room", "event coordinator"}
                found_services = sum(1 for s in services if any(ps in s.lower() for ps in premium_services))
                bonus += (found_services / len(premium_services)) * 0.2

        # Bonus por eventos soportados
        if data.get("supported_events"):
            events = data["supported_events"]
            if isinstance(events, list):
                target_events = {"wedding ceremony", "wedding reception", "rehearsal dinner"}
                found_events = sum(1 for e in events if any(te in e.lower() for te in target_events))
                bonus += (found_events / len(target_events)) * 0.2

        return min(bonus, 1.0)

    def score_optional(self, knowledge: Dict[str, Any], criteria: Dict[str, Any]) -> float:
        """Sistema de scoring mejorado que considera relaciones, compatibilidad, bonus y RAG"""
        data = knowledge.get("original_data", knowledge)
        opcionales = criteria.get("opcionales", [])

        # 1. Score base por criterios opcionales (30% del total)
        base_score = 0.0
        max_base_score = 0.0
        for campo in opcionales:
            expected = criteria.get(campo)
            actual = data.get(campo)
            if expected is None or actual is None:
                continue

            max_base_score += 0.3
            if isinstance(expected, str) and isinstance(actual, str):
                if expected.lower() in actual.lower():
                    base_score += 0.3
            elif isinstance(expected, list):
                if isinstance(actual, list):
                    matched = set(e.lower() for e in expected) & set(a.lower() for a in actual)
                    base_score += (len(matched) / len(expected)) * 0.3
                elif isinstance(actual, str):
                    base_score += (sum(1 for e in expected if e.lower() in actual.lower()) / len(expected)) * 0.3
            elif actual == expected:
                base_score += 0.3

        # Normalizar score base
        base_score = base_score / max_base_score if max_base_score > 0 else 0.0

        # 2. Score de compatibilidad (20% del total)
        compatibility_score = 0.0
        if base_score > 0.1:  # Solo calcular compatibilidad si el score base es bueno
            venue_id = data.get("url")
            if venue_id:
                related_venues = self.get_related_venues(venue_id, max_distance=1)
                if related_venues:
                    compatibility_scores = [
                        self.calculate_compatibility_score(knowledge, related)
                        for related in related_venues[:5]
                    ]
                    compatibility_score = sum(compatibility_scores) / len(compatibility_scores)

        # 3. Score de bonus (10% del total)
        bonus_score = 0.0
        if base_score > 0.1:
            bonus_score = self.calculate_bonus_score(data, criteria)

        # 4. Score de recomendaciones del RAG (40% del total)
        rag_score = 0.0
        rag_max_score = 0.0

        # Score de atmosphere recomendado (10%)
        if "recommended_atmosphere" in criteria and criteria["recommended_atmosphere"]:
            rag_max_score += 0.10
            atmosphere = data.get("atmosphere", [])
            if atmosphere:
                # Convertir a lista si es string
                if isinstance(atmosphere, str):
                    atmosphere = [atmosphere]
                # Hacer matching más flexible
                atmosphere_lower = [a.lower() for a in atmosphere]
                recommended_lower = [a.lower() for a in criteria["recommended_atmosphere"]]
                matched_atmosphere = set(atmosphere_lower) & set(recommended_lower)
                atmosphere_score = len(matched_atmosphere) / len(criteria["recommended_atmosphere"])
                rag_score += atmosphere_score * 0.10
                print(f"[VenueAgent] Score de atmosphere: {len(matched_atmosphere)}/{len(criteria['recommended_atmosphere'])} ({atmosphere_score:.2f})")
            else:
                print(f"[VenueAgent] DEBUG: Venue {data.get('title', 'Sin título')} no tiene campo 'atmosphere'. Campos disponibles: {list(data.keys())}")

        # Score de venue_type recomendado (10%)
        if "recommended_venue_type" in criteria and criteria["recommended_venue_type"]:
            rag_max_score += 0.10
            venue_type = data.get("venue_type", [])
            if venue_type:
                # Convertir a lista si es string
                if isinstance(venue_type, str):
                    venue_type = [venue_type]
                # Hacer matching más flexible
                venue_type_lower = [v.lower() for v in venue_type]
                recommended_lower = [v.lower() for v in criteria["recommended_venue_type"]]
                matched_venue_type = set(venue_type_lower) & set(recommended_lower)
                venue_type_score = len(matched_venue_type) / len(criteria["recommended_venue_type"])
                rag_score += venue_type_score * 0.10
                print(f"[VenueAgent] Score de venue_type: {len(matched_venue_type)}/{len(criteria['recommended_venue_type'])} ({venue_type_score:.2f})")
            else:
                print(f"[VenueAgent] DEBUG: Venue {data.get('title', 'Sin título')} no tiene campo 'venue_type'. Campos disponibles: {list(data.keys())}")

        # Score de services recomendados (10%)
        if "recommended_services" in criteria and criteria["recommended_services"]:
            rag_max_score += 0.10
            services = data.get("services", [])
            if services:
                # Convertir a lista si es string
                if isinstance(services, str):
                    services = [services]
                # Hacer matching más flexible
                services_lower = [s.lower() for s in services]
                recommended_lower = [s.lower() for s in criteria["recommended_services"]]
                matched_services = set(services_lower) & set(recommended_lower)
                services_score = len(matched_services) / len(criteria["recommended_services"])
                rag_score += services_score * 0.10
                print(f"[VenueAgent] Score de services: {len(matched_services)}/{len(criteria['recommended_services'])} ({services_score:.2f})")
            else:
                print(f"[VenueAgent] DEBUG: Venue {data.get('title', 'Sin título')} no tiene campo 'services'. Campos disponibles: {list(data.keys())}")

        # Score de supported_events recomendados (5%)
        if "recommended_supported_events" in criteria and criteria["recommended_supported_events"]:
            rag_max_score += 0.05
            supported_events = data.get("supported_events", [])
            if supported_events:
                matched_events = set(e.lower() for e in supported_events) & set(e.lower() for e in criteria["recommended_supported_events"])
                events_score = len(matched_events) / len(criteria["recommended_supported_events"])
                rag_score += events_score * 0.05
                print(f"[VenueAgent] Score de supported_events: {len(matched_events)}/{len(criteria['recommended_supported_events'])} ({events_score:.2f})")

        # Score de restrictions recomendadas (5%)
        if "recommended_restrictions" in criteria and criteria["recommended_restrictions"]:
            rag_max_score += 0.05
            restrictions = data.get("restrictions", [])
            if restrictions:
                matched_restrictions = set(r.lower() for r in restrictions) & set(r.lower() for r in criteria["recommended_restrictions"])
                restrictions_score = len(matched_restrictions) / len(criteria["recommended_restrictions"])
                rag_score += restrictions_score * 0.05
                print(f"[VenueAgent] Score de restrictions: {len(matched_restrictions)}/{len(criteria['recommended_restrictions'])} ({restrictions_score:.2f})")

        # Normalizar score del RAG solo si rag_max_score > 0
        if rag_max_score > 0:
            rag_score = (rag_score / rag_max_score) * 0.4
        else:
            rag_score = 0.0  # Si no hay recomendaciones del RAG, no contribuye al score

        # 5. Combinar scores con pesos
        final_score = (
            base_score * 0.3 +
            compatibility_score * 0.2 +
            bonus_score * 0.1 +
            rag_score
        )

        print(f"[VenueAgent] Score final para {data.get('title', 'Sin título')}: {final_score:.2f}")
        return min(final_score, 1.0)

    def find_venues(self, criteria: Dict[str, Any], urls: List[str] = None) -> List[Dict[str, Any]]:
        print("[VenueAgent] Iniciando búsqueda de venues...")
        self.setup_rules(criteria)

        # Obtener recomendaciones del RAG
        if "budget" in criteria and "guest_count" in criteria:
            print("[VenueAgent] Obteniendo recomendaciones del RAG...")
            print(f"[VenueAgent] Criterios para RAG: budget={criteria['budget']}, guest_count={criteria['guest_count']}")
            venue_recommendation = self.rag.get_venue_recommendation(
                budget=criteria["budget"],
                guest_count=criteria["guest_count"],
                style=criteria.get("style", "classic"),
                location=criteria.get("location", "")
            )
            
            # Actualizar criterios con las recomendaciones del RAG
            if venue_recommendation:
                print("[VenueAgent] Aplicando recomendaciones del RAG...")
                print(f"[VenueAgent] Recomendaciones del RAG: {json.dumps(venue_recommendation, indent=2)}")
                criteria["recommended_atmosphere"] = venue_recommendation["atmosphere"]
                criteria["recommended_venue_type"] = venue_recommendation["venue_type"]
                criteria["recommended_services"] = venue_recommendation["services"]
                criteria["recommended_supported_events"] = venue_recommendation["supported_events"]
                criteria["recommended_restrictions"] = venue_recommendation["restrictions"]
                criteria["capacity_range"] = venue_recommendation["capacity_range"]
                criteria["price_range"] = venue_recommendation["price_range"]
                print(f"[VenueAgent] Criterios actualizados con RAG - Atmosphere: {criteria['recommended_atmosphere']}")
                print(f"[VenueAgent] Criterios actualizados con RAG - Venue Type: {criteria['recommended_venue_type']}")
                print(f"[VenueAgent] Criterios actualizados con RAG - Services: {criteria['recommended_services']}")
                print(f"[VenueAgent] Criterios actualizados con RAG - Supported Events: {criteria['recommended_supported_events']}")
            else:
                print("[VenueAgent] ⚠️ No se obtuvieron recomendaciones del RAG")
        else:
            print("[VenueAgent] No se encontraron campos necesarios para RAG (budget y guest_count)")
            print(f"[VenueAgent] Criterios disponibles: {json.dumps(criteria, indent=2)}")

        # URLs por defecto si no se proporcionan
        if urls is None or not urls:
            urls = [
                "https://www.zola.com/wedding-vendors/search/wedding-venues?page=1"
            ]
            print(f"[VenueAgent] Usando URLs por defecto: {urls}")

        # Verificar si ya tenemos datos en el grafo
        print("[VenueAgent] Verificando datos existentes en el grafo...")
        venue_nodes = self.graph.query("venue")
        print(f"[VenueAgent] Nodos tipo 'venue' encontrados en el grafo: {len(venue_nodes)}")

        if not venue_nodes:
            print("[VenueAgent] No hay datos en el grafo, iniciando crawling...")
            for url in urls:
                self.crawler.enqueue_url(url)

            while self.crawler.to_visit and len(self.crawler.visited) < self.crawler.max_visits:
                next_url = self.crawler.to_visit.pop(0)
                self.crawler.crawl(next_url, context=criteria)
            
            # Guardar el grafo después del crawling
            print("[VenueAgent] Guardando grafo después del crawling...")
            self.graph.save_to_file("venues_graph.json")
            self.graph.clean_errors()
            
            # Intentar obtener los nodos nuevamente después del crawling
            venue_nodes = self.graph.query("venue")
            print(f"[VenueAgent] Nodos tipo 'venue' encontrados después del crawling: {len(venue_nodes)}")

        print("[VenueAgent] Procesando nodos tipo 'venue'...")
        candidates = []
        
        # Convertir los nodos del grafo a un formato manejable
        for node in venue_nodes:
            if isinstance(node, dict):
                candidates.append(node)
                # print(f"[VenueAgent] Nodo diccionario encontrado: {node.get('title', 'Sin título')}")
            elif isinstance(node, list):
                # Si es una lista, tomar el primer elemento si existe
                if node and isinstance(node[0], dict):
                    candidates.append(node[0])
                    print(f"[VenueAgent] Nodo lista convertido a diccionario: {node[0].get('title', 'Sin título')}")
                else:
                    print(f"[VenueAgent] Nodo lista ignorado: {node}")
        
        print(f"[VenueAgent] Se encontraron {len(candidates)} candidatos iniciales")

        valid = []
        for v in candidates:
            # Asegurarse de que tenemos los datos originales
            data = v.get("original_data", v)
            if not data:
                print(f"[VenueAgent] Advertencia: Nodo sin datos originales: {v.get('nombre', 'Desconocido')}")
                continue
                
            if self.expert.process_knowledge(data):
                valid.append((v, data))
                # print(f"[VenueAgent] Venue válido: {data.get('title', 'Sin título')}")

        print(f"[VenueAgent] {len(valid)} venues válidos tras reglas obligatorias")

        if not valid:
            print("[VenueAgent] Advertencia: No se encontraron venues válidos")
            print("[VenueAgent] Criterios aplicados:", criteria)
            return []

        scored = [(v[0], self.score_optional(v[1], criteria)) for v in valid]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Limitar a los 50 mejores resultados
        results = [v for v, _ in scored[:50]]
        
        # Actualizar patrones de éxito en RAG
        if results:
            print("[VenueAgent] Actualizando patrones de éxito en RAG...")
            pattern_data = {
                "style": criteria.get("style", "classic"),
                "location": criteria.get("location", ""),
                "capacity_range": criteria.get("capacity_range", [0, 0]),
                "price_range": criteria.get("price_range", [0, 0]),
                "atmosphere": criteria.get("recommended_atmosphere", []),
                "venue_type": criteria.get("recommended_venue_type", []),
                "services": criteria.get("recommended_services", []),
                "supported_events": criteria.get("recommended_supported_events", []),
                "restrictions": criteria.get("recommended_restrictions", [])
            }
            print(f"[VenueAgent] Datos del patrón a actualizar: {json.dumps(pattern_data, indent=2)}")
            self.rag.update_success_pattern(pattern_data, True)
            print("[VenueAgent] Patrón de éxito actualizado")
        
        print(f"[VenueAgent] Se retornan los {len(results)} mejores resultados")
        
        # Guardar el grafo antes de retornar
        # print("[VenueAgent] Guardando grafo antes de retornar...")
        # self.graph.save_to_file("venues_graph.json")
        
        return results

    def receive(self, message: Dict[str, Any]):
        """Procesa mensajes entrantes."""
        if message["tipo"] == "task":
            task_id = message["contenido"]["task_id"]
            parameters = message["contenido"]["parameters"]
            session_id = message["session_id"]
            
            # Obtener el grafo compartido si está disponible
            if "graph_data" in message["contenido"]:
                shared_graph = message["contenido"]["graph_data"].get("venue_graph")
                if shared_graph:
                    print("[VenueAgent] Usando grafo compartido del bus")
                    self.graph = shared_graph
            
            try:
                print(f"[VenueAgent] Procesando tarea de búsqueda de venue (task_id: {task_id})")
                # Procesar la tarea
                results = self.find_venues(parameters, [])  # Por ahora lista vacía de URLs
                
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
                print(f"[VenueAgent] Error procesando tarea: {str(e)}")
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
            print(f"[VenueAgent] Tipo de mensaje no reconocido: {message['tipo']}")