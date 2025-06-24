"""
Request Normalizer Utility

This module provides functions to normalize different request structures
to the standard format expected by the event planning system.
"""

from typing import Dict, Any, List, Optional
import re
from enum import Enum


class RequestNormalizer:
    """Normalizes request structures to the standard format."""
    
    def __init__(self):
        # Mapeo de campos alternativos a campos estándar
        self.field_mapping = {
            # Campos de presupuesto
            "presupuesto": "presupuesto_total",
            "budget": "presupuesto_total",
            "total_budget": "presupuesto_total",
            "event_budget": "presupuesto_total",
            
            # Campos de invitados
            "guest_count": "guest_count",
            "guests": "guest_count",
            "number_of_guests": "guest_count",
            "attendees": "guest_count",
            
            # Campos de estilo
            "style": "style",
            "event_style": "style",
            "theme": "style",
            "event_theme": "style",
            
            # Campos de venue
            "venue": "venue",
            "location": "venue",
            "place": "venue",
            "venue_type": "venue_type",
            "type": "venue_type",
            "venue_location": "location",
            "venue_capacity": "capacity",
            "capacity": "capacity",
            "guest_capacity": "capacity",
            "venue_atmosphere": "atmosphere",
            "atmosphere": "atmosphere",
            "venue_services": "services",
            "services": "services",
            
            # Campos de catering
            "catering": "catering",
            "food": "catering",
            "meal": "catering",
            "catering_services": "services",
            "catering_meal_types": "meal_types",
            "meal_types": "meal_types",
            "food_types": "meal_types",
            "catering_dietary_options": "dietary_options",
            "dietary_options": "dietary_options",
            "dietary_requirements": "dietary_options",
            "food_restrictions": "dietary_options",
            "catering_cuisines": "cuisines",
            "cuisines": "cuisines",
            "cuisine_types": "cuisines",
            
            # Campos de decor
            "decor": "decor",
            "decoration": "decor",
            "decor_services": "services",
            "decor_service_levels": "service_levels",
            "service_levels": "service_levels",
            "decor_floral_arrangements": "floral_arrangements",
            "floral_arrangements": "floral_arrangements",
            "flowers": "floral_arrangements",
            "decor_color_palette": "color_palette",
            "color_palette": "color_palette",
            "colors": "color_palette"
        }
        
        # Campos obligatorios por defecto para cada categoría
        self.default_obligatorios = {
            "venue": ["price", "capacity"],
            "catering": ["price"],
            "decor": ["price"]
        }
        
        # Estilo por defecto
        self.default_style = "classic"
    
    def normalize_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza cualquier estructura de request a la estructura estándar.
        
        Args:
            request: Request en cualquier formato
            
        Returns:
            Request normalizado con estructura estándar
        """
        print(f"[RequestNormalizer] Normalizando request: {request}")
        
        # Si ya tiene la estructura correcta, solo validar
        if "criterios" in request and isinstance(request["criterios"], dict):
            print("[RequestNormalizer] Request ya tiene estructura correcta, validando...")
            return self._validate_and_complete_criterios(request)
        
        # Crear estructura base
        normalized = {"criterios": {}}
        
        # Extraer campos del nivel raíz
        self._extract_root_fields(request, normalized["criterios"])
        
        # Extraer campos de venue
        self._extract_venue_fields(request, normalized["criterios"])
        
        # Extraer campos de catering
        self._extract_catering_fields(request, normalized["criterios"])
        
        # Extraer campos de decor
        self._extract_decor_fields(request, normalized["criterios"])
        
        # Completar campos faltantes
        self._complete_missing_fields(normalized["criterios"])
        
        # Validar y limpiar
        self._validate_and_clean(normalized["criterios"])
        
        print(f"[RequestNormalizer] Request normalizado: {normalized}")
        return normalized
    
    def _extract_root_fields(self, request: Dict[str, Any], criterios: Dict[str, Any]):
        """Extrae campos del nivel raíz del request."""
        for key, value in request.items():
            normalized_key = self.field_mapping.get(key, key)
            
            if normalized_key in ["presupuesto_total", "guest_count", "style"]:
                criterios[normalized_key] = value
    
    def _extract_venue_fields(self, request: Dict[str, Any], criterios: Dict[str, Any]):
        """Extrae campos relacionados con venue."""
        venue_data = {}
        
        # Buscar datos de venue en diferentes ubicaciones
        venue_sources = [
            request.get("venue"),
            request.get("location"),
            request.get("place"),
            {k: v for k, v in request.items() if k.startswith("venue_") or k in ["venue_type", "type", "capacity", "atmosphere", "services"]}
        ]
        
        for source in venue_sources:
            if source and isinstance(source, dict):
                for key, value in source.items():
                    normalized_key = self.field_mapping.get(key, key)
                    if normalized_key in ["venue_type", "location", "capacity", "atmosphere", "services"]:
                        venue_data[normalized_key] = value
        
        # Extraer campos individuales del nivel raíz
        for key, value in request.items():
            normalized_key = self.field_mapping.get(key, key)
            if normalized_key in ["venue_type", "location", "capacity", "atmosphere", "services"]:
                venue_data[normalized_key] = value
        
        if venue_data:
            criterios["venue"] = venue_data
    
    def _extract_catering_fields(self, request: Dict[str, Any], criterios: Dict[str, Any]):
        """Extrae campos relacionados con catering."""
        catering_data = {}
        
        # Buscar datos de catering en diferentes ubicaciones
        catering_sources = [
            request.get("catering"),
            request.get("food"),
            request.get("meal"),
            {k: v for k, v in request.items() if k.startswith("catering_") or k in ["meal_types", "dietary_options", "cuisines"]}
        ]
        
        for source in catering_sources:
            if source and isinstance(source, dict):
                for key, value in source.items():
                    normalized_key = self.field_mapping.get(key, key)
                    if normalized_key in ["meal_types", "dietary_options", "cuisines", "services"]:
                        catering_data[normalized_key] = value
        
        # Extraer campos individuales del nivel raíz
        for key, value in request.items():
            normalized_key = self.field_mapping.get(key, key)
            if normalized_key in ["meal_types", "dietary_options", "cuisines"]:
                catering_data[normalized_key] = value
        
        if catering_data:
            criterios["catering"] = catering_data
    
    def _extract_decor_fields(self, request: Dict[str, Any], criterios: Dict[str, Any]):
        """Extrae campos relacionados con decor."""
        decor_data = {}
        
        # Buscar datos de decor en diferentes ubicaciones
        decor_sources = [
            request.get("decor"),
            request.get("decoration"),
            {k: v for k, v in request.items() if k.startswith("decor_") or k in ["service_levels", "floral_arrangements", "color_palette"]}
        ]
        
        for source in decor_sources:
            if source and isinstance(source, dict):
                for key, value in source.items():
                    normalized_key = self.field_mapping.get(key, key)
                    if normalized_key in ["service_levels", "floral_arrangements", "color_palette", "services"]:
                        decor_data[normalized_key] = value
        
        # Extraer campos individuales del nivel raíz
        for key, value in request.items():
            normalized_key = self.field_mapping.get(key, key)
            if normalized_key in ["service_levels", "floral_arrangements", "color_palette"]:
                decor_data[normalized_key] = value
        
        if decor_data:
            criterios["decor"] = decor_data
    
    def _complete_missing_fields(self, criterios: Dict[str, Any]):
        """Completa campos faltantes con valores por defecto."""
        # Presupuesto total
        if "presupuesto_total" not in criterios:
            if "presupuesto" in criterios:
                criterios["presupuesto_total"] = criterios["presupuesto"]
            elif "budget" in criterios:
                criterios["presupuesto_total"] = criterios["budget"]
        
        # Guest count
        if "guest_count" not in criterios:
            if "guests" in criterios:
                criterios["guest_count"] = criterios["guests"]
            elif "attendees" in criterios:
                criterios["guest_count"] = criterios["attendees"]
        
        # Style
        if "style" not in criterios:
            criterios["style"] = self.default_style
        
        # Completar categorías faltantes
        for category, default_obligatorios in self.default_obligatorios.items():
            if category not in criterios:
                criterios[category] = {"obligatorios": default_obligatorios}
            elif "obligatorios" not in criterios[category]:
                criterios[category]["obligatorios"] = default_obligatorios
    
    def _validate_and_clean(self, criterios: Dict[str, Any]):
        """Valida y limpia los criterios."""
        # Convertir valores de enum a strings si es necesario
        self._convert_enum_values(criterios)
        
        # Normalizar arrays
        self._normalize_arrays(criterios)
        
        # Validar tipos de datos
        self._validate_data_types(criterios)
    
    def _convert_enum_values(self, data: Any):
        """Convierte valores de enum a strings."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, Enum):
                    data[key] = value.value
                elif isinstance(value, (dict, list)):
                    self._convert_enum_values(value)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, Enum):
                    data[i] = item.value
                elif isinstance(item, (dict, list)):
                    self._convert_enum_values(item)
    
    def _normalize_arrays(self, data: Any):
        """Normaliza arrays para asegurar consistencia."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    self._normalize_arrays(value)
        elif isinstance(data, list):
            # Asegurar que todos los elementos sean del mismo tipo
            if data and all(isinstance(item, str) for item in data):
                # Normalizar strings
                data[:] = [str(item).strip() for item in data if item]
            elif data and all(isinstance(item, (int, float)) for item in data):
                # Normalizar números
                data[:] = [float(item) for item in data if item is not None]
    
    def _validate_data_types(self, criterios: Dict[str, Any]):
        """Valida tipos de datos críticos."""
        # Validar presupuesto_total
        if "presupuesto_total" in criterios:
            try:
                criterios["presupuesto_total"] = float(criterios["presupuesto_total"])
            except (ValueError, TypeError):
                print(f"[RequestNormalizer] Warning: presupuesto_total inválido: {criterios['presupuesto_total']}")
                criterios["presupuesto_total"] = 0
        
        # Validar guest_count
        if "guest_count" in criterios:
            try:
                criterios["guest_count"] = int(criterios["guest_count"])
            except (ValueError, TypeError):
                print(f"[RequestNormalizer] Warning: guest_count inválido: {criterios['guest_count']}")
                criterios["guest_count"] = 0
    
    def _validate_and_complete_criterios(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Valida y completa criterios que ya tienen la estructura correcta."""
        criterios = request["criterios"]
        
        # Completar campos faltantes
        self._complete_missing_fields(criterios)
        
        # Validar y limpiar
        self._validate_and_clean(criterios)
        
        return request


# Instancia global del normalizador
normalizer = RequestNormalizer()


def normalize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Función de conveniencia para normalizar requests.
    
    Args:
        request: Request en cualquier formato
        
    Returns:
        Request normalizado con estructura estándar
    """
    return normalizer.normalize_request(request) 