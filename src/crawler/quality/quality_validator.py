from typing import Dict, Any, List, Tuple
import re
from datetime import datetime, timedelta, timezone
import json

class DataQualityValidator:
    def __init__(self):
        # Campos críticos que deben estar presentes (con variaciones de nombres)
        self.critical_fields = {
            "venue": {
                "title": ["title", "nombre", "name"],
                "capacity": ["capacity", "capacidad", "guest_capacity"],
                "location": ["location", "ubication", "address", "place"],
                "price": ["price", "precio", "cost", "rate"]
            },
            "catering": {
                "title": ["title", "nombre", "name"],
                "services": ["services", "servicios", "offerings"],
                "location": ["location", "ubication", "address", "place"],
                "price": ["price", "precio", "cost", "rate"]
            },
            "decor": {
                "title": ["title", "nombre", "name"],
                "location": ["location", "ubication", "address", "place"],
                "price": ["price", "precio", "cost", "rate"],
                "service_levels": ["service_levels", "niveles_servicio", "services"]
            }
        }
        
        # Patrones de validación para cada campo
        self.validation_patterns = {
            "title": {
                "min_length": 2,  # Reducido de 3
                "max_length": 200,  # Aumentado de 100
                "required": True
            },
            "capacity": {
                "min_value": 1,  # Reducido de 10
                "max_value": 50000,  # Aumentado de 10000
                "required": True
            },
            "price": {
                "min_value": 0,
                "required": True
            },
            "location": {
                "min_length": 5,  # Reducido de 10
                "required": True
            },
            "services": {
                "min_items": 0,  # Reducido de 1
                "required": True
            }
        }
        
        # Umbrales de calidad más flexibles
        self.quality_thresholds = {
            "completeness": 0.5,  # Reducido de 0.7 (50% de campos críticos presentes)
            "freshness": 90,      # Aumentado de 30 (90 días máximo de antigüedad)
            "accuracy": 0.6       # Reducido de 0.8 (60% de campos válidos)
        }

    def validate_data_quality(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Valida la calidad de los datos extraídos."""
        validation_result = {
            "is_complete": False,
            "is_fresh": False,
            "is_accurate": False,
            "completeness_score": 0.0,
            "freshness_score": 0.0,
            "accuracy_score": 0.0,
            "overall_score": 0.0,
            "missing_fields": [],
            "invalid_fields": [],
            "needs_enrichment": False,
            "enrichment_sources": []
        }
        
        # 1. Validar completitud
        completeness_result = self._validate_completeness(data, data_type)
        validation_result.update(completeness_result)
        
        # 2. Validar frescura
        freshness_result = self._validate_freshness(data)
        validation_result.update(freshness_result)
        
        # 3. Validar precisión
        accuracy_result = self._validate_accuracy(data, data_type)
        validation_result.update(accuracy_result)
        
        # 4. Calcular score general
        validation_result["overall_score"] = (
            validation_result["completeness_score"] * 0.4 +
            validation_result["freshness_score"] * 0.3 +
            validation_result["accuracy_score"] * 0.3
        )
        
        # 5. Determinar si necesita enriquecimiento
        validation_result["needs_enrichment"] = (
            validation_result["overall_score"] < 0.7 or
            len(validation_result["missing_fields"]) > 2 or
            not validation_result["is_fresh"]
        )
        
        # 6. Sugerir fuentes de enriquecimiento
        if validation_result["needs_enrichment"]:
            validation_result["enrichment_sources"] = self._suggest_enrichment_sources(data, data_type)
        
        return validation_result

    def _validate_completeness(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Valida la completitud de los datos."""
        required_fields = self.critical_fields.get(data_type, {})
        present_fields = 0
        missing_fields = []
        
        for field_category, aliases in required_fields.items():
            field_found = False
            for alias in aliases:
                if alias in data and data[alias] is not None:
                    # Verificar que el campo no esté vacío
                    if isinstance(data[alias], str) and data[alias].strip():
                        present_fields += 1
                        field_found = True
                        break
                    elif isinstance(data[alias], (list, dict)) and data[alias]:
                        present_fields += 1
                        field_found = True
                        break
                    elif isinstance(data[alias], (int, float)) and data[alias] > 0:
                        present_fields += 1
                        field_found = True
                        break
            
            if not field_found:
                missing_fields.append(field_category)
        
        completeness_score = present_fields / len(required_fields) if required_fields else 0.0
        
        return {
            "is_complete": completeness_score >= self.quality_thresholds["completeness"],
            "completeness_score": completeness_score,
            "missing_fields": missing_fields
        }

    def _validate_freshness(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida la frescura de los datos."""
        timestamp = data.get("timestamp")
        if not timestamp:
            return {
                "is_fresh": False,
                "freshness_score": 0.0,
                "age_days": float('inf')
            }
        
        try:
            if isinstance(timestamp, str):
                # Manejar diferentes formatos de timestamp
                if 'Z' in timestamp:
                    timestamp = timestamp.replace('Z', '+00:00')
                elif timestamp.endswith('UTC'):
                    timestamp = timestamp.replace('UTC', '+00:00')
                
                data_time = datetime.fromisoformat(timestamp)
            else:
                data_time = timestamp
            
            current_time = datetime.now(timezone.utc)
            
            # Si el timestamp no tiene zona horaria, asumir UTC
            if data_time.tzinfo is None:
                data_time = data_time.replace(tzinfo=timezone.utc)
            
            age_days = (current_time - data_time).days
            
            freshness_score = max(0, 1 - (age_days / self.quality_thresholds["freshness"]))
            is_fresh = age_days <= self.quality_thresholds["freshness"]
            
            return {
                "is_fresh": is_fresh,
                "freshness_score": freshness_score,
                "age_days": age_days
            }
        except Exception as e:
            print(f"[VALIDATOR] Error procesando timestamp '{timestamp}': {str(e)}")
            return {
                "is_fresh": False,
                "freshness_score": 0.0,
                "age_days": float('inf')
            }

    def _validate_accuracy(self, data: Dict[str, Any], data_type: str) -> Dict[str, Any]:
        """Valida la precisión de los datos."""
        valid_fields = 0
        total_fields = 0
        invalid_fields = []
        
        # Verificar campos según patrones de validación
        for field, pattern in self.validation_patterns.items():
            # Buscar el campo en los datos usando alias
            field_found = False
            field_value = None
            
            # Buscar en campos críticos de este tipo de dato
            if data_type in self.critical_fields:
                for aliases in self.critical_fields[data_type].values():
                    for alias in aliases:
                        if alias in data and data[alias] is not None:
                            field_value = data[alias]
                            field_found = True
                            break
                    if field_found:
                        break
            
            # Si no se encontró en campos críticos, buscar directamente
            if not field_found and field in data:
                field_value = data[field]
                field_found = True
            
            if field_found:
                total_fields += 1
                if self._validate_field_pattern(field_value, pattern):
                    valid_fields += 1
                else:
                    invalid_fields.append(field)
        
        accuracy_score = valid_fields / total_fields if total_fields > 0 else 0.0
        
        return {
            "is_accurate": accuracy_score >= self.quality_thresholds["accuracy"],
            "accuracy_score": accuracy_score,
            "invalid_fields": invalid_fields
        }

    def _validate_field_pattern(self, value: Any, pattern: Dict[str, Any]) -> bool:
        """Valida un campo específico según su patrón."""
        try:
            if pattern.get("required", False) and (value is None or value == ""):
                return False
            
            if isinstance(value, str):
                if "min_length" in pattern and len(value) < pattern["min_length"]:
                    return False
                if "max_length" in pattern and len(value) > pattern["max_length"]:
                    return False
            
            elif isinstance(value, (int, float)):
                if "min_value" in pattern and value < pattern["min_value"]:
                    return False
                if "max_value" in pattern and value > pattern["max_value"]:
                    return False
            
            elif isinstance(value, list):
                if "min_items" in pattern and len(value) < pattern["min_items"]:
                    return False
            
            return True
        except Exception:
            return False

    def _suggest_enrichment_sources(self, data: Dict[str, Any], data_type: str) -> List[str]:
        """Sugiere fuentes de enriquecimiento basadas en los datos faltantes."""
        sources = []
        missing_fields = self._validate_completeness(data, data_type)["missing_fields"]
        
        # Fuentes específicas por tipo de dato
        if data_type == "venue":
            if "price" in missing_fields or "capacity" in missing_fields:
                sources.extend([
                    "https://www.theknot.com/marketplace",
                    "https://www.weddingwire.com/venues",
                    "https://www.zola.com/wedding-vendors/wedding-venues"
                ])
            if "services" in missing_fields:
                sources.append("https://www.zola.com/wedding-vendors/wedding-venues")
        
        elif data_type == "catering":
            if "services" in missing_fields or "price" in missing_fields:
                sources.extend([
                    "https://www.theknot.com/marketplace/catering",
                    "https://www.zola.com/wedding-vendors/wedding-catering"
                ])
        
        elif data_type == "decor":
            if "service_levels" in missing_fields or "price" in missing_fields:
                sources.extend([
                    "https://www.theknot.com/marketplace/florists",
                    "https://www.zola.com/wedding-vendors/wedding-florists"
                ])
        
        # Fuentes generales
        sources.extend([
            "https://www.google.com/search",
            "https://www.yelp.com/search"
        ])
        
        return sources

    def get_enrichment_priority(self, data: Dict[str, Any], data_type: str) -> int:
        """Determina la prioridad de enriquecimiento (1-10, 10 = máxima prioridad)."""
        validation = self.validate_data_quality(data, data_type)
        
        priority = 1
        
        # Prioridad basada en score general
        if validation["overall_score"] < 0.3:
            priority += 4
        elif validation["overall_score"] < 0.5:
            priority += 3
        elif validation["overall_score"] < 0.7:
            priority += 2
        else:
            priority += 1
        
        # Prioridad basada en campos críticos faltantes
        critical_fields = self.critical_fields.get(data_type, {})
        critical_missing = len([f for f in validation["missing_fields"] 
                              if f in critical_fields])
        priority += critical_missing * 2
        
        # Prioridad basada en frescura
        if not validation["is_fresh"]:
            priority += 2
        
        return min(priority, 10) 