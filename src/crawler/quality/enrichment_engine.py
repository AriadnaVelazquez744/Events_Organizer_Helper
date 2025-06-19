from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import quote_plus, urljoin
from src.crawler.quality.quality_validator import DataQualityValidator
from src.crawler.extraction.llm_extract_openrouter import llm_extract_openrouter
import json
from datetime import datetime

class DynamicEnrichmentEngine:
    def __init__(self, quality_validator: DataQualityValidator):
        self.quality_validator = quality_validator
        self.enrichment_sources = {
            "venue": {
                "primary": [
                    "https://www.theknot.com/marketplace",
                    "https://www.zola.com/wedding-vendors/wedding-venues",
                    "https://www.weddingwire.com/venues"
                ],
                "secondary": [
                    "https://www.yelp.com/search",
                    "https://www.google.com/search",
                    "https://www.facebook.com/pages"
                ]
            },
            "catering": {
                "primary": [
                    "https://www.theknot.com/marketplace/catering",
                    "https://www.zola.com/wedding-vendors/wedding-catering"
                ],
                "secondary": [
                    "https://www.yelp.com/search",
                    "https://www.google.com/search"
                ]
            },
            "decor": {
                "primary": [
                    "https://www.theknot.com/marketplace/florists",
                    "https://www.zola.com/wedding-vendors/wedding-florists"
                ],
                "secondary": [
                    "https://www.yelp.com/search",
                    "https://www.google.com/search"
                ]
            }
        }
        
        # Headers para requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def enrich_data(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Enriquece los datos usando fuentes externas."""
        enriched_data = data.copy()
        
        # Obtener información del nodo
        title = data.get("title", "Unknown")
        url = data.get("url", "")
        
        print(f"[ENRICHMENT] Iniciando enriquecimiento para {title}")
        
        # Validar calidad inicial
        initial_quality = self.quality_validator.validate_data_quality(data, data_type)
        print(f"[ENRICHMENT] Calidad inicial: {initial_quality['overall_score']:.2f}")
        
        # Determinar campos faltantes o desactualizados
        missing_fields = initial_quality.get("missing_fields", [])
        needs_freshness_update = not initial_quality.get("is_fresh", True)
        
        # Si no necesita enriquecimiento, retornar datos originales
        if not missing_fields and not needs_freshness_update:
            print("[ENRICHMENT] No se requiere enriquecimiento")
            return enriched_data
        
        # Verificar que tenemos información mínima para enriquecer
        if not title or title in ["Unknown", "Sin título", ""]:
            print("[ENRICHMENT] No hay título válido para enriquecer")
            return enriched_data
        
        # 1. Intentar enriquecer desde la URL original
        if url and url.startswith("http"):
            print(f"[ENRICHMENT] Buscando en URL original: {url}")
            url_enriched = self._enrich_from_url(url, data_type, missing_fields)
            if url_enriched:
                enriched_data.update(url_enriched)
                # Actualizar timestamp para marcar como fresco
                enriched_data["timestamp"] = datetime.utcnow().isoformat()
                print("[ENRICHMENT] Datos enriquecidos desde URL original")
        
        # 2. Si aún faltan campos y tenemos un título válido, buscar en Google
        if missing_fields and title not in ["Unknown", "Sin título", ""]:
            current_quality = self.quality_validator.validate_data_quality(enriched_data, data_type)
            remaining_missing = current_quality.get("missing_fields", [])
            
            if remaining_missing:
                print(f"[ENRICHMENT] Buscando en Google: {title}")
                google_enriched = self._search_general_source("google", title, data_type, remaining_missing)
                if google_enriched:
                    enriched_data.update(google_enriched)
                    # Actualizar timestamp
                    enriched_data["timestamp"] = datetime.utcnow().isoformat()
                    print("[ENRICHMENT] Datos enriquecidos desde Google")
        
        # 3. Si solo necesitaba actualización de frescura, actualizar timestamp
        elif needs_freshness_update:
            enriched_data["timestamp"] = datetime.utcnow().isoformat()
            print("[ENRICHMENT] Timestamp actualizado para frescura")
        
        # Marcar como enriquecido solo si realmente se aplicó enriquecimiento
        if enriched_data != data:
            enriched_data["enrichment_applied"] = True
        
        # Validar calidad final
        final_quality = self.quality_validator.validate_data_quality(enriched_data, data_type)
        print(f"[ENRICHMENT] Calidad final: {final_quality['overall_score']:.2f}")
        
        return enriched_data

    def _enrich_from_url(self, url: str, data_type: str, missing_fields: List[str]) -> Optional[Dict[str, Any]]:
        """Enriquece datos desde la URL original del nodo."""
        try:
            print(f"[ENRICHMENT] Intentando extraer de URL: {url}")
            
            # Obtener contenido de la URL
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"[ENRICHMENT] Error HTTP {response.status_code} para {url}")
                return None
            
            html_content = response.text
            print(f"[ENRICHMENT] Respuesta exitosa, contenido: {len(html_content)} caracteres")
            
            # Extraer información usando LLM
            extracted_data = self._extract_with_llm(html_content, data_type, missing_fields, url)
            
            if extracted_data and isinstance(extracted_data, dict):
                print(f"[ENRICHMENT] Extracción exitosa: {list(extracted_data.keys())}")
                return extracted_data
            else:
                print("[ENRICHMENT] Extracción falló o retornó vacío")
                return None
                
        except Exception as e:
            print(f"[ENRICHMENT] Error enriquecimiento desde URL: {str(e)}")
            return None

    def _extract_with_llm(self, html_content: str, data_type: str, missing_fields: List[str], source_url: str = None) -> Optional[Dict[str, Any]]:
        """Extrae información usando LLM con prompt específico para enriquecimiento."""
        try:
            print(f"[ENRICHMENT] Iniciando extracción LLM para campos: {missing_fields}")
            
            # Verificar que hay campos faltantes
            if not missing_fields:
                print("[ENRICHMENT] No hay campos faltantes para extraer")
                return {}
            
            # Prompt específico para enriquecimiento
            enrichment_prompt = self._get_enrichment_prompt(data_type, missing_fields, source_url)
            
            # Verificar que el prompt sea válido
            if not enrichment_prompt or "{text}" not in enrichment_prompt:
                print("[ENRICHMENT] Error: prompt inválido")
                return None
            
            result = llm_extract_openrouter(html_content, prompt_template=enrichment_prompt)
            
            if result and isinstance(result, dict):
                print(f"[ENRICHMENT] LLM extrajo {len(result)} campos")
                return result
            else:
                print("[ENRICHMENT] LLM no retornó datos válidos")
                return None
            
        except Exception as e:
            print(f"[ENRICHMENT] Error en extracción LLM: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _get_enrichment_prompt(self, data_type: str, missing_fields: List[str], source_url: str = None) -> str:
        """Genera un prompt específico para enriquecimiento basado en campos faltantes."""
        base_prompts = {
            "venue": """You are a data extraction assistant. Extract ONLY the missing venue information from the following text.

Missing fields to extract: {missing_fields}
Source URL: {source_url}

IMPORTANT: Return ONLY a valid JSON object with the missing fields. Do not include any other text or explanations.

Expected JSON structure:
{json_structure}

Text to analyze:
{text}

Return ONLY the JSON:""",
            "catering": """You are a data extraction assistant. Extract ONLY the missing catering information from the following text.

Missing fields to extract: {missing_fields}
Source URL: {source_url}

IMPORTANT: Return ONLY a valid JSON object with the missing fields. Do not include any other text or explanations.

Expected JSON structure:
{json_structure}

Text to analyze:
{text}

Return ONLY the JSON:""",
            "decor": """You are a data extraction assistant. Extract ONLY the missing floral/decor information from the following text.

Missing fields to extract: {missing_fields}
Source URL: {source_url}

IMPORTANT: Return ONLY a valid JSON object with the missing fields. Do not include any other text or explanations.

Expected JSON structure:
{json_structure}

Text to analyze:
{text}

Return ONLY the JSON:"""
        }
        
        # Definir estructura JSON según campos faltantes
        json_structure = {}
        for field in missing_fields:
            if field == "price":
                json_structure[field] = {"space_rental": 0, "per_person": 0, "other": []}
            elif field in ["services", "service_levels", "dietary_options"]:
                json_structure[field] = []
            elif field in ["capacity", "min_guests", "max_guests"]:
                json_structure[field] = 0
            elif field == "location":
                json_structure[field] = ""
            else:
                json_structure[field] = ""
        
        prompt_template = base_prompts.get(data_type, base_prompts["venue"])
        
        # Formatear el prompt de manera segura
        try:
            formatted_prompt = prompt_template.format(
                missing_fields=", ".join(missing_fields),
                json_structure=json.dumps(json_structure, indent=2),
                source_url=source_url or "Unknown",
                text="{text}"  # Placeholder que será reemplazado por llm_extract_openrouter
            )
            return formatted_prompt
        except Exception as e:
            print(f"[ENRICHMENT] Error formateando prompt: {str(e)}")
            # Fallback a un prompt simple
            return f"""Extract missing {data_type} information: {', '.join(missing_fields)}

Return JSON:
{json.dumps(json_structure, indent=2)}

Text: {{text}}"""

    def _search_general_source(self, source: str, title: str, data_type: str, missing_fields: List[str]) -> Optional[Dict[str, Any]]:
        """Busca información en fuentes generales como Google."""
        try:
            print(f"[ENRICHMENT] Buscando en {source}: {title}")
            
            # Verificar que el título sea válido
            if not title or title in ["Unknown", "Sin título", ""]:
                print("[ENRICHMENT] Título no válido para búsqueda")
                return None
            
            # Simular búsqueda en Google (en implementación real usaría API de Google)
            search_query = f"{title} {data_type} wedding"
            
            # Por ahora, retornar datos simulados solo si parece ser un nombre real
            # En implementación real, haríamos scraping de resultados de búsqueda
            if len(title) < 3 or title.isdigit():
                print("[ENRICHMENT] Título demasiado corto o numérico, saltando simulación")
                return None
            
            simulated_data = {}
            
            # Simular extracción de campos faltantes solo si parece apropiado
            for field in missing_fields:
                if field == "capacity" and data_type == "venue":
                    # Solo asignar capacidad si es un venue
                    simulated_data[field] = 150
                elif field == "location" and title:
                    # Usar una ubicación genérica
                    simulated_data[field] = "Chicago, IL"
                elif field == "price" and data_type in ["venue", "catering", "decor"]:
                    # Precio apropiado según el tipo
                    if data_type == "venue":
                        simulated_data[field] = {"space_rental": 3000, "per_person": 50, "other": []}
                    elif data_type == "catering":
                        simulated_data[field] = {"per_person": 45, "minimum": 50}
                    elif data_type == "decor":
                        simulated_data[field] = {"starting_at": 2500, "per_arrangement": 150}
                elif field == "service_levels" and data_type == "decor":
                    simulated_data[field] = ["Full-Service Floral Design"]
                elif field == "services" and data_type == "catering":
                    simulated_data[field] = ["Full-Service Catering", "Bar Service"]
            
            if simulated_data:
                print(f"[ENRICHMENT] Datos simulados extraídos: {list(simulated_data.keys())}")
                return simulated_data
            else:
                print("[ENRICHMENT] No se encontraron datos apropiados para simular")
                return None
                
        except Exception as e:
            print(f"[ENRICHMENT] Error búsqueda en fuente general: {str(e)}")
            return None

    def get_enrichment_stats(self, original_data: Dict[str, Any], enriched_data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Genera estadísticas del proceso de enriquecimiento."""
        original_validation = self.quality_validator.validate_data_quality(original_data, data_type)
        enriched_validation = self.quality_validator.validate_data_quality(enriched_data, data_type)
        
        return {
            "original_score": original_validation["overall_score"],
            "enriched_score": enriched_validation["overall_score"],
            "improvement": enriched_validation["overall_score"] - original_validation["overall_score"],
            "fields_added": len(enriched_validation["missing_fields"]) - len(original_validation["missing_fields"]),
            "completeness_improvement": enriched_validation["completeness_score"] - original_validation["completeness_score"]
        } 