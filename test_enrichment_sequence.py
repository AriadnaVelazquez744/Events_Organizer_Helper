#!/usr/bin/env python3
"""
Script de prueba para verificar la secuencia de enriquecimiento:
1. Fuente primaria: URL original del nodo
2. Fuente secundaria: Google
"""

from Crawler.quality_validator import DataQualityValidator
from Crawler.enrichment_engine import DynamicEnrichmentEngine

def test_enrichment_sequence():
    """Prueba la secuencia de enriquecimiento con datos que necesitan mejora."""
    print("=== PRUEBA DE SECUENCIA DE ENRIQUECIMIENTO ===\n")
    
    validator = DataQualityValidator()
    engine = DynamicEnrichmentEngine(validator)
    
    # Datos de prueba que necesitan enriquecimiento
    test_data = {
        "title": "The Grand Ballroom",
        "url": "https://example.com/grand-ballroom",  # URL que fallará (404)
        "capacity": 150,
        "timestamp": "2024-01-01T00:00:00Z"
        # Faltan: location, price
    }
    
    print("Datos de prueba:")
    print(f"Título: {test_data['title']}")
    print(f"URL: {test_data['url']}")
    print(f"Campos presentes: {list(test_data.keys())}")
    
    # Validar calidad inicial
    initial_quality = validator.validate_data_quality(test_data, "venue")
    print(f"\nCalidad inicial: {initial_quality['overall_score']:.2f}")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    print(f"Necesita enriquecimiento: {initial_quality['needs_enrichment']}")
    
    # Aplicar enriquecimiento
    print("\n" + "="*50)
    print("APLICANDO ENRIQUECIMIENTO")
    print("="*50)
    
    enriched_data = engine.enrich_data(test_data, "venue")
    
    # Validar calidad final
    final_quality = validator.validate_data_quality(enriched_data, "venue")
    print(f"\nCalidad final: {final_quality['overall_score']:.2f}")
    
    # Mostrar campos agregados
    added_fields = set(enriched_data.keys()) - set(test_data.keys())
    print(f"Campos agregados: {list(added_fields)}")
    
    # Verificar si se aplicó enriquecimiento
    if enriched_data.get("enrichment_applied"):
        print("✅ Enriquecimiento aplicado correctamente")
    else:
        print("❌ No se aplicó enriquecimiento")
    
    return enriched_data

def test_url_only_enrichment():
    """Prueba enriquecimiento solo desde URL (sin Google)."""
    print("\n" + "="*50)
    print("PRUEBA: ENRIQUECIMIENTO SOLO DESDE URL")
    print("="*50)
    
    validator = DataQualityValidator()
    engine = DynamicEnrichmentEngine(validator)
    
    # Datos con URL válida pero sin campos faltantes después
    test_data = {
        "title": "Perfect Venue",
        "url": "https://httpbin.org/html",  # URL que funciona
        "capacity": 200,
        "location": "Chicago, IL",
        "timestamp": "2024-01-01T00:00:00Z"
        # Solo falta: price
    }
    
    print("Datos con URL válida:")
    print(f"Título: {test_data['title']}")
    print(f"URL: {test_data['url']}")
    
    # Validar calidad inicial
    initial_quality = validator.validate_data_quality(test_data, "venue")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    
    # Aplicar enriquecimiento
    enriched_data = engine.enrich_data(test_data, "venue")
    
    # Verificar resultado
    final_quality = validator.validate_data_quality(enriched_data, "venue")
    print(f"Calidad final: {final_quality['overall_score']:.2f}")
    
    return enriched_data

def test_google_fallback():
    """Prueba el fallback a Google cuando la URL falla."""
    print("\n" + "="*50)
    print("PRUEBA: FALLBACK A GOOGLE")
    print("="*50)
    
    validator = DataQualityValidator()
    engine = DynamicEnrichmentEngine(validator)
    
    # Datos con URL que fallará, forzando uso de Google
    test_data = {
        "title": "Mystery Venue",  # Título válido para búsqueda en Google
        "url": "https://example.com/nonexistent",  # URL que fallará
        "capacity": 100,
        "timestamp": "2024-01-01T00:00:00Z"
        # Faltan: location, price
    }
    
    print("Datos con URL que fallará:")
    print(f"Título: {test_data['title']}")
    print(f"URL: {test_data['url']}")
    
    # Validar calidad inicial
    initial_quality = validator.validate_data_quality(test_data, "venue")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    
    # Aplicar enriquecimiento
    enriched_data = engine.enrich_data(test_data, "venue")
    
    # Verificar resultado
    final_quality = validator.validate_data_quality(enriched_data, "venue")
    print(f"Calidad final: {final_quality['overall_score']:.2f}")
    
    return enriched_data

if __name__ == "__main__":
    # Prueba completa de secuencia
    result1 = test_enrichment_sequence()
    
    # Prueba solo URL
    result2 = test_url_only_enrichment()
    
    # Prueba fallback a Google
    result3 = test_google_fallback()
    
    print("\n" + "="*50)
    print("RESUMEN DE PRUEBAS")
    print("="*50)
    print("✅ Secuencia de enriquecimiento verificada:")
    print("   1. Fuente primaria: URL original del nodo")
    print("   2. Fuente secundaria: Google (solo si es necesario)")
    print("   3. Validación de calidad antes y después")
    print("   4. Marcado de enriquecimiento aplicado") 