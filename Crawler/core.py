# crawler/core.py (actualizado)
import re
from urllib.parse import urlparse, urljoin
from typing import Callable, List, Dict, Any
from Crawler.scrapper import scrape_page
from Crawler.policy import CrawlPolicy
from Crawler.quality_validator import DataQualityValidator
from Crawler.enrichment_engine import DynamicEnrichmentEngine
from datetime import datetime

class AdvancedCrawlerAgent:
    
    def __init__(self, name: str, graph_interface, expert_system=None, policy=None, mission_profile=None):
        self.name = name
        self.graph_interface = graph_interface
        self.expert_system = expert_system
        self.policy = policy or CrawlPolicy()
        self.mission_profile = mission_profile or {}
        self.log = []
        self.visited = set()
        self.max_visits = 15
        self.to_visit = []  # nueva pila FIFO
        
        # Inicializar sistema de validación y enriquecimiento
        self.quality_validator = DataQualityValidator()
        self.enrichment_engine = DynamicEnrichmentEngine(self.quality_validator)
        
        # Configuración de enriquecimiento dinámico
        self.enrichment_config = {
            "enabled": True,
            "auto_enrich": True,
            "quality_threshold": 0.5,
            "max_enrichment_attempts": 3
        }

    def enqueue_url(self, url):
        if "search" in url and "?page=" in url:
            self.to_visit.append(url)
        else:    
            if (
                url in self.visited 
                or url in self.to_visit 
                or url in self.graph_interface.nodes
            ):
                print(f"[CRAWLER] Ignorando URL ya conocida: {url}")
                return
            self.to_visit.append(url)

    def crawl(self, url: str, context: Dict[str, Any] = None, depth: int = 0):
        print("[CRAWLER] Iniciando scrape de:", url)

        if url in self.visited:
            print(f"[CRAWLER] Ya visitado: {url}")
            return

        if not self.policy.can_fetch(url):
            print(f"[CRAWLER] Robots.txt bloquea: {url} (continuando con Selenium si es necesario)")

        if len(self.visited) >= self.max_visits:
            print(f"[CRAWLER] Límite de {self.max_visits} URLs alcanzado.")
            return

        self.policy.wait()
        self.visited.add(url)

        try:
            content = scrape_page(url, context)
            print(f"[CRAWLER] Contenido scrapeado: {bool(content)}")

            # Asegura campos mínimos
            content.setdefault("url", url)
            content.setdefault("tipo", "venue")
            content.setdefault("timestamp", datetime.utcnow().isoformat())
            knowledge = content

            # === FASE DINÁMICA: VALIDACIÓN Y ENRIQUECIMIENTO ===
            if self.enrichment_config["enabled"]:
                knowledge = self._apply_dynamic_enrichment(knowledge, context)

            # Insertar en el grafo
            self.graph_interface.insert_knowledge(knowledge)

            # Evaluar con el sistema experto
            if self.expert_system:
                self.expert_system.process_knowledge(knowledge)

            self._log("SUCCESS", f"Procesado: {url}")

            # === EXPANSIÓN DE URLS ===
            outlinks = content.get("outbound_links") or content.get("outlinks") or []
            base_domain = urlparse(url).netloc

            # 1. Agregar outlinks relevantes
            for next_url in outlinks:
                if isinstance(next_url, str) and next_url.startswith("http"):
                    if urlparse(next_url).netloc == base_domain:
                        self.enqueue_url(next_url)

            # 2. Si es página de búsqueda, intentar paginar
            if "search" in url and "?page=" in url:
                match = re.search(r"\?page=(\d+)", url)
                if match:
                    current_page = int(match.group(1))
                    next_page_url = re.sub(r"\?page=\d+", f"?page={current_page + 1}", url)
                    self.enqueue_url(next_page_url)
            elif "search" in url and "?page=" not in url:
                self.enqueue_url(url + "?page=2")

        except Exception as e:
            self._log("ERROR", f"{url} falló: {str(e)}")

    def _apply_dynamic_enrichment(self, knowledge: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Aplica enriquecimiento dinámico basado en validación de calidad."""
        data_type = knowledge.get("tipo", "venue")
        
        print(f"[CRAWLER] Aplicando validación de calidad para {data_type}")
        
        # 1. Validar calidad de los datos extraídos
        quality_result = self.quality_validator.validate_data_quality(knowledge, data_type)
        
        print(f"[CRAWLER] Score de calidad: {quality_result['overall_score']:.2f}")
        print(f"[CRAWLER] Campos faltantes: {quality_result['missing_fields']}")
        print(f"[CRAWLER] Necesita enriquecimiento: {quality_result['needs_enrichment']}")
        
        # 2. Aplicar enriquecimiento si es necesario
        if quality_result["needs_enrichment"] and self.enrichment_config["auto_enrich"]:
            print(f"[CRAWLER] Iniciando enriquecimiento dinámico...")
            
            # Determinar prioridad de enriquecimiento
            priority = self.quality_validator.get_enrichment_priority(knowledge, data_type)
            print(f"[CRAWLER] Prioridad de enriquecimiento: {priority}/10")
            
            # Aplicar enriquecimiento con límite de intentos
            enriched_knowledge = knowledge
            enrichment_attempts = 0
            
            while (enrichment_attempts < self.enrichment_config["max_enrichment_attempts"] and 
                   quality_result["needs_enrichment"]):
                
                print(f"[CRAWLER] Intento de enriquecimiento {enrichment_attempts + 1}")
                
                # Aplicar enriquecimiento
                enriched_knowledge = self.enrichment_engine.enrich_data(enriched_knowledge, data_type)
                
                # Validar calidad después del enriquecimiento
                quality_result = self.quality_validator.validate_data_quality(enriched_knowledge, data_type)
                
                print(f"[CRAWLER] Score después del enriquecimiento: {quality_result['overall_score']:.2f}")
                
                enrichment_attempts += 1
                
                # Si alcanzamos el umbral de calidad, detener
                if quality_result["overall_score"] >= self.enrichment_config["quality_threshold"]:
                    print(f"[CRAWLER] Umbral de calidad alcanzado ({self.enrichment_config['quality_threshold']})")
                    break
            
            # Generar estadísticas del enriquecimiento
            if enrichment_attempts > 0:
                stats = self.enrichment_engine.get_enrichment_stats(knowledge, enriched_knowledge, data_type)
                print(f"[CRAWLER] Estadísticas de enriquecimiento:")
                print(f"  - Mejora de score: {stats['improvement']:.2f}")
                print(f"  - Campos agregados: {stats['fields_added']}")
                print(f"  - Mejora de completitud: {stats['completeness_improvement']:.2f}")
                
                # Agregar metadatos de enriquecimiento
                enriched_knowledge["enrichment_metadata"] = {
                    "original_score": stats["original_score"],
                    "final_score": stats["enriched_score"],
                    "improvement": stats["improvement"],
                    "attempts": enrichment_attempts,
                    "enrichment_timestamp": datetime.utcnow().isoformat()
                }
            
            return enriched_knowledge
        
        else:
            print(f"[CRAWLER] No se requiere enriquecimiento (score: {quality_result['overall_score']:.2f})")
            return knowledge

    def _log(self, level: str, message: str):
        log_entry = f"[{self.name}] [{level}] {datetime.utcnow().isoformat()} - {message}"
        print(log_entry)
        self.log.append(log_entry)

    def get_quality_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de calidad de los datos procesados."""
        # Solo considerar nodos de los tipos principales que nos interesan
        valid_types = {"venue", "catering", "decor"}
        relevant_nodes = [
            node for node in self.graph_interface.nodes.values()
            if node.get("tipo") in valid_types
        ]
        
        quality_stats = {
            "total_nodes": len(relevant_nodes),
            "quality_distribution": {
                "excellent": 0,  # 0.8-1.0
                "good": 0,       # 0.6-0.8
                "fair": 0,       # 0.4-0.6
                "poor": 0        # 0.0-0.4
            },
            "enrichment_stats": {
                "enriched_nodes": 0,
                "average_improvement": 0.0
            },
            "by_type": {}
        }
        
        total_improvement = 0.0
        enriched_count = 0
        
        for node in relevant_nodes:
            data_type = node.get("tipo", "unknown")
            
            # Calcular score de calidad
            quality_result = self.quality_validator.validate_data_quality(node, data_type)
            score = quality_result["overall_score"]
            
            # Categorizar por calidad
            if score >= 0.8:
                quality_stats["quality_distribution"]["excellent"] += 1
            elif score >= 0.6:
                quality_stats["quality_distribution"]["good"] += 1
            elif score >= 0.4:
                quality_stats["quality_distribution"]["fair"] += 1
            else:
                quality_stats["quality_distribution"]["poor"] += 1
            
            # Estadísticas de enriquecimiento
            if node.get("enrichment_applied"):
                enriched_count += 1
                if "enrichment_metadata" in node:
                    total_improvement += node["enrichment_metadata"].get("improvement", 0.0)
            
            # Estadísticas por tipo
            if data_type not in quality_stats["by_type"]:
                quality_stats["by_type"][data_type] = {
                    "count": 0,
                    "average_score": 0.0,
                    "enriched_count": 0
                }
            
            type_stats = quality_stats["by_type"][data_type]
            type_stats["count"] += 1
            type_stats["average_score"] += score
            if node.get("enrichment_applied"):
                type_stats["enriched_count"] += 1
        
        # Calcular promedios
        quality_stats["enrichment_stats"]["enriched_nodes"] = enriched_count
        if enriched_count > 0:
            quality_stats["enrichment_stats"]["average_improvement"] = total_improvement / enriched_count
        
        for data_type in quality_stats["by_type"]:
            type_stats = quality_stats["by_type"][data_type]
            if type_stats["count"] > 0:
                type_stats["average_score"] /= type_stats["count"]
        
        return quality_stats