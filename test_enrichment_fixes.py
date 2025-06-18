#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema de validación y enriquecimiento dinámico.
"""

import json
from Crawler.quality_validator import DataQualityValidator
from Crawler.enrichment_engine import DynamicEnrichmentEngine

def test_quality_validator():
    """Prueba el validador de calidad con datos reales."""
    print("=== PRUEBA DEL VALIDADOR DE CALIDAD ===")
    
    validator = DataQualityValidator()
    
    # Datos de prueba para venue
    venue_data = {
        "title": "Beautiful Wedding Venue",
        "capacity": 200,
        "location": "123 Main St, Chicago, IL",
        "price": {"space_rental": 5000, "per_person": 75},
        "timestamp": "2024-12-15T10:00:00Z"
    }
    
    print("Datos de prueba venue:")
    print(json.dumps(venue_data, indent=2))
    
    # Validar calidad
    quality_result = validator.validate_data_quality(venue_data, "venue")
    print("\nResultado de validación:")
    print(json.dumps(quality_result, indent=2))
    
    # Datos de prueba para catering
    catering_data = {
        "title": "Premium Catering Service",
        "services": ["Full Catering", "Bar Service"],
        "ubication": "456 Oak Ave, Chicago, IL",
        "price": 45,
        "timestamp": "2024-12-15T10:00:00Z"
    }
    
    print("\nDatos de prueba catering:")
    print(json.dumps(catering_data, indent=2))
    
    quality_result = validator.validate_data_quality(catering_data, "catering")
    print("\nResultado de validación:")
    print(json.dumps(quality_result, indent=2))
    
    # Datos de prueba para decor
    decor_data = {
        "title": "Elegant Floral Design",
        "ubication": "789 Pine St, Chicago, IL",
        "price": 2500,
        "service_levels": ["Full-Service Floral Design"],
        "timestamp": "2024-12-15T10:00:00Z"
    }
    
    print("\nDatos de prueba decor:")
    print(json.dumps(decor_data, indent=2))
    
    quality_result = validator.validate_data_quality(decor_data, "decor")
    print("\nResultado de validación:")
    print(json.dumps(quality_result, indent=2))

def test_enrichment_engine():
    """Prueba el motor de enriquecimiento."""
    print("\n=== PRUEBA DEL MOTOR DE ENRIQUECIMIENTO ===")
    
    validator = DataQualityValidator()
    engine = DynamicEnrichmentEngine(validator)
    
    # Datos incompletos para enriquecer
    incomplete_venue = {
        "title": "Mystery Venue",
        "url": "https://example.com/venue",
        "timestamp": "2024-01-01T00:00:00Z"
        # Faltan: capacity, location, price
    }
    
    print("Datos incompletos para enriquecer:")
    print(json.dumps(incomplete_venue, indent=2))
    
    # Intentar enriquecer
    print("\nIntentando enriquecer datos...")
    enriched_data = engine.enrich_data(incomplete_venue, "venue")
    
    print("\nDatos enriquecidos:")
    print(json.dumps(enriched_data, indent=2))
    
    # Obtener estadísticas
    stats = engine.get_enrichment_stats(incomplete_venue, enriched_data, "venue")
    print("\nEstadísticas de enriquecimiento:")
    print(json.dumps(stats, indent=2))

def test_with_real_data():
    """Prueba con datos reales del grafo."""
    print("\n=== PRUEBA CON DATOS REALES ===")
    
    # Simular datos reales extraídos
    real_venue_data = {
        "title": "The Grand Ballroom",
        "capacity": 150,
        "location": "Downtown Chicago",
        "price": {"space_rental": 3500},
        "venue_type": "Ballroom",
        "atmosphere": ["Elegant", "Formal"],
        "services": ["Catering", "Bar Service"],
        "supported_events": ["Wedding Ceremony", "Wedding Reception"],
        "restrictions": [],
        "timestamp": "2024-12-15T10:00:00Z"
    }
    
    validator = DataQualityValidator()
    quality_result = validator.validate_data_quality(real_venue_data, "venue")
    
    print("Datos reales de venue:")
    print(json.dumps(real_venue_data, indent=2))
    print("\nCalidad de datos reales:")
    print(json.dumps(quality_result, indent=2))

if __name__ == "__main__":
    test_quality_validator()
    test_enrichment_engine()
    test_with_real_data()
    
    print("\n=== PRUEBAS COMPLETADAS ===") 