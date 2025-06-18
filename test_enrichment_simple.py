#!/usr/bin/env python3
"""
Script de prueba simple para verificar el enriquecimiento corregido.
"""

from crawler.quality.quality_validator import DataQualityValidator
from crawler.quality.enrichment_engine import DynamicEnrichmentEngine

def test_enrichment_with_good_data():
    """Prueba enriquecimiento con datos que tienen información útil."""
    print("=== PRUEBA DE ENRIQUECIMIENTO CON DATOS ÚTILES ===")
    
    validator = DataQualityValidator()
    engine = DynamicEnrichmentEngine(validator)
    
    # Datos con información útil
    good_venue_data = {
        "title": "The Grand Ballroom",
        "url": "https://example.com/grand-ballroom",
        "capacity": 150,
        "timestamp": "2024-01-01T00:00:00Z"
        # Faltan: location, price
    }
    
    print("Datos con información útil:")
    print(f"Título: {good_venue_data['title']}")
    print(f"URL: {good_venue_data['url']}")
    
    # Validar calidad inicial
    initial_quality = validator.validate_data_quality(good_venue_data, "venue")
    print(f"Calidad inicial: {initial_quality['overall_score']:.2f}")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    
    # Intentar enriquecer
    print("\nIntentando enriquecer...")
    enriched_data = engine.enrich_data(good_venue_data, "venue")
    
    # Validar calidad final
    final_quality = validator.validate_data_quality(enriched_data, "venue")
    print(f"Calidad final: {final_quality['overall_score']:.2f}")
    
    # Mostrar campos agregados
    added_fields = set(enriched_data.keys()) - set(good_venue_data.keys())
    print(f"Campos agregados: {list(added_fields)}")
    
    return enriched_data

def test_enrichment_with_bad_data():
    """Prueba enriquecimiento con datos sin información útil."""
    print("\n=== PRUEBA DE ENRIQUECIMIENTO CON DATOS SIN INFORMACIÓN ÚTIL ===")
    
    validator = DataQualityValidator()
    engine = DynamicEnrichmentEngine(validator)
    
    # Datos sin información útil
    bad_venue_data = {
        "title": "Unknown",
        "url": "",
        "timestamp": "2024-01-01T00:00:00Z"
    }
    
    print("Datos sin información útil:")
    print(f"Título: {bad_venue_data['title']}")
    print(f"URL: {bad_venue_data['url']}")
    
    # Validar calidad inicial
    initial_quality = validator.validate_data_quality(bad_venue_data, "venue")
    print(f"Calidad inicial: {initial_quality['overall_score']:.2f}")
    
    # Intentar enriquecer
    print("\nIntentando enriquecer...")
    enriched_data = engine.enrich_data(bad_venue_data, "venue")
    
    # Verificar que no se aplicó enriquecimiento
    if enriched_data == bad_venue_data:
        print("✅ Correcto: No se aplicó enriquecimiento a datos sin información útil")
    else:
        print("❌ Error: Se aplicó enriquecimiento a datos sin información útil")
    
    return enriched_data

if __name__ == "__main__":
    # Prueba con datos útiles
    good_result = test_enrichment_with_good_data()
    
    # Prueba con datos sin información útil
    bad_result = test_enrichment_with_bad_data()
    
    print("\n=== PRUEBAS COMPLETADAS ===") 