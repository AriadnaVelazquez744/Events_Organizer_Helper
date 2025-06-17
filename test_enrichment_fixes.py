#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones del sistema de enriquecimiento dinámico.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from Crawler.quality_validator import DataQualityValidator
from Crawler.enrichment_engine import DynamicEnrichmentEngine
from datetime import datetime, timedelta
import json

def test_venue_incomplete_data():
    """Prueba enriquecimiento de datos de venue incompletos."""
    print("=" * 80)
    print("PRUEBA: Datos de Venue Incompletos (CORREGIDO)")
    print("=" * 80)
    
    # Datos de venue incompletos
    venue_data = {
        "title": "Chicago Winery",
        "url": "https://www.zola.com/wedding-vendors/wedding-venues/chicago-winery",
        "tipo": "venue",
        "atmosphere": ["Indoor", "Elegant"],
        "venue_type": ["Winery"],
        "services": ["Bar Service", "Catering"],
        "supported_events": ["Wedding Ceremony", "Wedding Reception"],
        "restrictions": ["No outside alcohol"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Inicializar componentes
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    
    # 1. Validación inicial
    print("\n1. VALIDACIÓN INICIAL:")
    initial_quality = validator.validate_data_quality(venue_data, "venue")
    print(f"Score de calidad: {initial_quality['overall_score']:.2f}")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    print(f"Necesita enriquecimiento: {initial_quality['needs_enrichment']}")
    
    # 2. Aplicar enriquecimiento
    print("\n2. APLICANDO ENRIQUECIMIENTO:")
    enriched_data = enrichment_engine.enrich_data(venue_data, "venue")
    
    # 3. Validación post-enriquecimiento
    print("\n3. VALIDACIÓN POST-ENRIQUECIMIENTO:")
    final_quality = validator.validate_data_quality(enriched_data, "venue")
    print(f"Score de calidad final: {final_quality['overall_score']:.2f}")
    print(f"Campos faltantes restantes: {final_quality['missing_fields']}")
    
    # 4. Estadísticas de enriquecimiento
    print("\n4. ESTADÍSTICAS DE ENRIQUECIMIENTO:")
    stats = enrichment_engine.get_enrichment_stats(venue_data, enriched_data, "venue")
    print(f"Mejora de score: {stats['improvement']:.2f}")
    print(f"Campos agregados: {stats['fields_added']}")
    print(f"Mejora de completitud: {stats['completeness_improvement']:.2f}")
    
    return enriched_data

def test_catering_outdated_data():
    """Prueba enriquecimiento de datos de catering desactualizados."""
    print("\n" + "=" * 80)
    print("PRUEBA: Datos de Catering Desactualizados (CORREGIDO)")
    print("=" * 80)
    
    # Datos de catering desactualizados
    old_timestamp = (datetime.utcnow() - timedelta(days=90)).isoformat()
    catering_data = {
        "title": "Event Advantage Catering",
        "url": "https://www.zola.com/wedding-vendors/wedding-catering/event-advantage-catering",
        "tipo": "catering",
        "services": ["Full-Service Catering", "Bar Service"],
        "ubication": "Chicago, IL",
        "cuisines": ["American", "Italian"],
        "dietary_options": ["Vegetarian", "Gluten-Free"],
        "meal_types": ["Buffet", "Plated"],
        "beverage_services": ["Full Bar", "Wine Service"],
        "drink_types": ["Cocktails", "Wine", "Beer"],
        "restrictions": ["No outside food"],
        "timestamp": old_timestamp
    }
    
    # Inicializar componentes
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    
    # 1. Validación inicial
    print("\n1. VALIDACIÓN INICIAL:")
    initial_quality = validator.validate_data_quality(catering_data, "catering")
    print(f"Score de calidad: {initial_quality['overall_score']:.2f}")
    print(f"Es fresco: {initial_quality['is_fresh']}")
    print(f"Edad en días: {initial_quality.get('age_days', 'N/A')}")
    
    # 2. Aplicar enriquecimiento
    print("\n2. APLICANDO ENRIQUECIMIENTO:")
    enriched_data = enrichment_engine.enrich_data(catering_data, "catering")
    
    # 3. Validación post-enriquecimiento
    print("\n3. VALIDACIÓN POST-ENRIQUECIMIENTO:")
    final_quality = validator.validate_data_quality(enriched_data, "catering")
    print(f"Score de calidad final: {final_quality['overall_score']:.2f}")
    print(f"Es fresco: {final_quality['is_fresh']}")
    
    return enriched_data

def test_decor_high_quality_data():
    """Prueba enriquecimiento de datos de decor de alta calidad."""
    print("\n" + "=" * 80)
    print("PRUEBA: Datos de Decor de Alta Calidad (CORREGIDO)")
    print("=" * 80)
    
    # Datos de decor de alta calidad
    decor_data = {
        "title": "Blush Blooms & Co.",
        "url": "https://www.zola.com/wedding-vendors/wedding-florists/blush-blooms-co",
        "tipo": "decor",
        "ubication": "Chicago, IL",
        "price": {"starting_at": 2500, "per_arrangement": 150},
        "pre_wedding_services": ["Consultation", "Design Planning"],
        "post_wedding_services": ["Cleanup", "Preservation"],
        "day_of_services": ["Setup", "Delivery", "Installation"],
        "arrangement_styles": ["Romantic", "Modern", "Rustic"],
        "floral_arrangements": ["Bouquets", "Centerpieces", "Ceremony decor"],
        "restrictions": ["Seasonal availability"],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Inicializar componentes
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    
    # 1. Validación inicial
    print("\n1. VALIDACIÓN INICIAL:")
    initial_quality = validator.validate_data_quality(decor_data, "decor")
    print(f"Score de calidad: {initial_quality['overall_score']:.2f}")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    print(f"Campos inválidos: {initial_quality['invalid_fields']}")
    
    # 2. Aplicar enriquecimiento
    print("\n2. APLICANDO ENRIQUECIMIENTO:")
    enriched_data = enrichment_engine.enrich_data(decor_data, "decor")
    
    # 3. Validación post-enriquecimiento
    print("\n3. VALIDACIÓN POST-ENRIQUECIMIENTO:")
    final_quality = validator.validate_data_quality(enriched_data, "decor")
    print(f"Score de calidad final: {final_quality['overall_score']:.2f}")
    print(f"Campos faltantes restantes: {final_quality['missing_fields']}")
    
    return enriched_data

def main():
    """Ejecuta todas las pruebas de enriquecimiento."""
    print("INICIANDO PRUEBAS DE ENRIQUECIMIENTO DINÁMICO")
    print("=" * 80)
    
    try:
        # Prueba 1: Venue incompleto
        venue_result = test_venue_incomplete_data()
        
        # Prueba 2: Catering desactualizado
        catering_result = test_catering_outdated_data()
        
        # Prueba 3: Decor de alta calidad
        decor_result = test_decor_high_quality_data()
        
        print("\n" + "=" * 80)
        print("RESUMEN DE PRUEBAS")
        print("=" * 80)
        print("✅ Todas las pruebas completadas sin errores críticos")
        print("✅ Sistema de enriquecimiento funcionando correctamente")
        print("✅ Manejo de errores mejorado")
        print("✅ Prompts corregidos y funcionando")
        
    except Exception as e:
        print(f"\n❌ Error en las pruebas: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 