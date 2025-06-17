#!/usr/bin/env python3
"""
Script de prueba para el sistema de enriquecimiento dinámico.
Demuestra cómo el sistema detecta y corrige automáticamente datos incompletos o desactualizados.
"""

import json
from datetime import datetime, timedelta, timezone
from Crawler.quality_validator import DataQualityValidator
from Crawler.enrichment_engine import DynamicEnrichmentEngine
from Crawler.monitoring import DataQualityMonitor

def test_incomplete_venue_data():
    """Prueba con datos de venue incompletos."""
    print("="*60)
    print("PRUEBA: Datos de Venue Incompletos")
    print("="*60)
    
    # Datos incompletos de un venue con URL específica
    incomplete_venue = {
        "title": "Chicago Winery",
        "tipo": "venue",
        "url": "https://www.zola.com/wedding-vendors/wedding-venues/chicago-winery",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Faltan: capacity, location, price, services
    }
    
    # Inicializar componentes
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    monitor = DataQualityMonitor(validator)
    
    # Validar calidad inicial
    print("\n1. VALIDACIÓN INICIAL:")
    initial_quality = validator.validate_data_quality(incomplete_venue, "venue")
    print(f"Score de calidad: {initial_quality['overall_score']:.2f}")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    print(f"Necesita enriquecimiento: {initial_quality['needs_enrichment']}")
    
    # Monitorear calidad
    monitoring_result = monitor.monitor_data_quality(incomplete_venue, "venue", incomplete_venue["url"])
    print(f"\nAlertas generadas: {len(monitoring_result['alerts_generated'])}")
    
    # Aplicar enriquecimiento
    print("\n2. APLICANDO ENRIQUECIMIENTO:")
    enriched_venue = enrichment_engine.enrich_data(incomplete_venue, "venue")
    
    # Validar calidad después del enriquecimiento
    print("\n3. VALIDACIÓN POST-ENRIQUECIMIENTO:")
    final_quality = validator.validate_data_quality(enriched_venue, "venue")
    print(f"Score de calidad final: {final_quality['overall_score']:.2f}")
    print(f"Campos faltantes restantes: {final_quality['missing_fields']}")
    
    # Mostrar estadísticas de enriquecimiento
    stats = enrichment_engine.get_enrichment_stats(incomplete_venue, enriched_venue, "venue")
    print(f"\n4. ESTADÍSTICAS DE ENRIQUECIMIENTO:")
    print(f"Mejora de score: {stats['improvement']:.2f}")
    print(f"Campos agregados: {stats['fields_added']}")
    print(f"Mejora de completitud: {stats['completeness_improvement']:.2f}")
    
    return enriched_venue

def test_stale_catering_data():
    """Prueba con datos de catering desactualizados."""
    print("\n" + "="*60)
    print("PRUEBA: Datos de Catering Desactualizados")
    print("="*60)
    
    # Datos desactualizados de catering con URL específica
    stale_catering = {
        "title": "Event Advantage Catering",
        "tipo": "catering",
        "url": "https://www.zola.com/wedding-vendors/wedding-catering/event-advantage-catering",
        "services": ["Wedding catering", "Corporate events"],
        "ubication": "New York, NY",
        "price": {"per_person": 45},
        "timestamp": (datetime.now(timezone.utc) - timedelta(days=90)).isoformat(),  # 90 días atrás
        "cuisines": ["American", "Italian"],
        "dietary_options": ["Vegetarian"]
    }
    
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    monitor = DataQualityMonitor(validator)
    
    # Validar calidad inicial
    print("\n1. VALIDACIÓN INICIAL:")
    initial_quality = validator.validate_data_quality(stale_catering, "catering")
    print(f"Score de calidad: {initial_quality['overall_score']:.2f}")
    print(f"Es fresco: {initial_quality['is_fresh']}")
    print(f"Edad en días: {initial_quality.get('age_days', 0)}")
    
    # Monitorear calidad
    monitoring_result = monitor.monitor_data_quality(stale_catering, "catering", stale_catering["url"])
    print(f"\nAlertas generadas: {len(monitoring_result['alerts_generated'])}")
    for alert in monitoring_result['alerts_generated']:
        print(f"  - {alert['message']}")
    
    # Aplicar enriquecimiento
    print("\n2. APLICANDO ENRIQUECIMIENTO:")
    enriched_catering = enrichment_engine.enrich_data(stale_catering, "catering")
    
    # Validar calidad después del enriquecimiento
    print("\n3. VALIDACIÓN POST-ENRIQUECIMIENTO:")
    final_quality = validator.validate_data_quality(enriched_catering, "catering")
    print(f"Score de calidad final: {final_quality['overall_score']:.2f}")
    print(f"Es fresco: {final_quality['is_fresh']}")
    
    return enriched_catering

def test_low_quality_decor_data():
    """Prueba con datos de decor de baja calidad."""
    print("\n" + "="*60)
    print("PRUEBA: Datos de Decor de Baja Calidad")
    print("="*60)
    
    # Datos de baja calidad con URL específica
    low_quality_decor = {
        "title": "Blush Blooms & Co.",
        "tipo": "decor",
        "url": "https://www.zola.com/wedding-vendors/wedding-florists/blush-blooms-co",
        "ubication": "City",     # Ubicación muy vaga
        "price": "Contact us",   # Precio no numérico
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Faltan muchos campos críticos
    }
    
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    monitor = DataQualityMonitor(validator)
    
    # Validar calidad inicial
    print("\n1. VALIDACIÓN INICIAL:")
    initial_quality = validator.validate_data_quality(low_quality_decor, "decor")
    print(f"Score de calidad: {initial_quality['overall_score']:.2f}")
    print(f"Campos faltantes: {initial_quality['missing_fields']}")
    print(f"Campos inválidos: {initial_quality['invalid_fields']}")
    
    # Monitorear calidad
    monitoring_result = monitor.monitor_data_quality(low_quality_decor, "decor", low_quality_decor["url"])
    print(f"\nAlertas generadas: {len(monitoring_result['alerts_generated'])}")
    for alert in monitoring_result['alerts_generated']:
        print(f"  - {alert['severity'].upper()}: {alert['message']}")
    
    # Aplicar enriquecimiento
    print("\n2. APLICANDO ENRIQUECIMIENTO:")
    enriched_decor = enrichment_engine.enrich_data(low_quality_decor, "decor")
    
    # Validar calidad después del enriquecimiento
    print("\n3. VALIDACIÓN POST-ENRIQUECIMIENTO:")
    final_quality = validator.validate_data_quality(enriched_decor, "decor")
    print(f"Score de calidad final: {final_quality['overall_score']:.2f}")
    print(f"Campos faltantes restantes: {final_quality['missing_fields']}")
    
    return enriched_decor

def test_monitoring_system():
    """Prueba el sistema de monitoreo completo."""
    print("\n" + "="*60)
    print("PRUEBA: Sistema de Monitoreo")
    print("="*60)
    
    validator = DataQualityValidator()
    monitor = DataQualityMonitor(validator)
    
    # Simular múltiples datos de diferentes calidades con URLs reales
    test_data = [
        {
            "title": "Good Venue", 
            "tipo": "venue", 
            "url": "https://www.zola.com/wedding-vendors/wedding-venues/good-venue",
            "capacity": 200, 
            "location": "123 Main St", 
            "price": {"space_rental": 5000}
        },
        {
            "title": "Bad Venue", 
            "tipo": "venue",
            "url": "https://www.zola.com/wedding-vendors/wedding-venues/bad-venue"
        },  # Muy incompleto
        {
            "title": "Old Venue", 
            "tipo": "venue", 
            "url": "https://www.zola.com/wedding-vendors/wedding-venues/old-venue",
            "capacity": 150, 
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=100)).isoformat()
        },
        {
            "title": "Good Catering", 
            "tipo": "catering", 
            "url": "https://www.zola.com/wedding-vendors/wedding-catering/good-catering",
            "services": ["Wedding"], 
            "ubication": "Downtown", 
            "price": {"per_person": 50}
        },
        {
            "title": "Bad Catering", 
            "tipo": "catering",
            "url": "https://www.zola.com/wedding-vendors/wedding-catering/bad-catering"
        },  # Muy incompleto
    ]
    
    print("\n1. PROCESANDO MÚLTIPLES DATOS:")
    for i, data in enumerate(test_data):
        print(f"\nProcesando dato {i+1}: {data['title']}")
        monitoring_result = monitor.monitor_data_quality(data, data["tipo"], data["url"])
        print(f"  Score: {monitoring_result['quality_score']:.2f}")
        print(f"  Alertas: {len(monitoring_result['alerts_generated'])}")
    
    # Obtener tendencias
    print("\n2. ANÁLISIS DE TENDENCIAS:")
    trends = monitor.get_quality_trends(hours=1)  # Última hora
    print(f"Total de registros: {trends.get('total_records', 0)}")
    print(f"Score promedio: {trends.get('overall_avg_score', 0):.2f}")
    
    # Obtener alertas activas
    print("\n3. ALERTAS ACTIVAS:")
    active_alerts = monitor.get_active_alerts()
    print(f"Total de alertas: {len(active_alerts)}")
    for alert in active_alerts:
        print(f"  - {alert['severity'].upper()}: {alert['message']}")
    
    # Generar reporte completo
    print("\n4. REPORTE COMPLETO:")
    full_report = monitor.export_monitoring_report(hours=1)
    print(f"Alertas de alta severidad: {full_report['summary']['high_severity_alerts']}")
    print(f"Recomendaciones del sistema: {len(full_report['recommendations'])}")

def main():
    """Ejecuta todas las pruebas del sistema dinámico."""
    print("🚀 INICIANDO PRUEBAS DEL SISTEMA DE ENRIQUECIMIENTO DINÁMICO")
    print("="*80)
    
    try:
        # Prueba 1: Datos incompletos
        enriched_venue = test_incomplete_venue_data()
        
        # Prueba 2: Datos desactualizados
        enriched_catering = test_stale_catering_data()
        
        # Prueba 3: Datos de baja calidad
        enriched_decor = test_low_quality_decor_data()
        
        # Prueba 4: Sistema de monitoreo
        test_monitoring_system()
        
        print("\n" + "="*80)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("="*80)
        
        # Mostrar resumen de resultados
        print("\n📊 RESUMEN DE RESULTADOS:")
        print(f"  - Venue enriquecido: {enriched_venue.get('title', 'N/A')}")
        print(f"  - Catering enriquecido: {enriched_catering.get('title', 'N/A')}")
        print(f"  - Decor enriquecido: {enriched_decor.get('title', 'N/A')}")
        
        # Verificar si el enriquecimiento fue exitoso
        validator = DataQualityValidator()
        
        venue_quality = validator.validate_data_quality(enriched_venue, "venue")
        catering_quality = validator.validate_data_quality(enriched_catering, "catering")
        decor_quality = validator.validate_data_quality(enriched_decor, "decor")
        
        print(f"\n🎯 CALIDAD FINAL:")
        print(f"  - Venue: {venue_quality['overall_score']:.2f}")
        print(f"  - Catering: {catering_quality['overall_score']:.2f}")
        print(f"  - Decor: {decor_quality['overall_score']:.2f}")
        
        # Calcular mejora promedio
        improvements = [
            venue_quality['overall_score'],
            catering_quality['overall_score'],
            decor_quality['overall_score']
        ]
        avg_improvement = sum(improvements) / len(improvements)
        print(f"  - Promedio: {avg_improvement:.2f}")
        
        if avg_improvement > 0.6:
            print("\n🎉 El sistema de enriquecimiento dinámico está funcionando correctamente!")
        else:
            print("\n⚠️ El sistema necesita ajustes para mejorar la calidad de datos.")
        
    except Exception as e:
        print(f"\n❌ ERROR EN LAS PRUEBAS: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 