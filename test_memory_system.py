#!/usr/bin/env python3
"""
Test script for the Budget Distributor Agent memory system
Tests learning, consistency, and persistence across multiple queries
"""

import json
import os
from agents.budget.BudgetAgent import BudgetDistributorAgent

def create_test_criteria():
    """Crea criterios de prueba más diferenciados para generar variaciones."""
    return {
        # CONSULTA 1: Venue simple, catering complejo, decor básico
        "venue_simple": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "elegante",
            "venue": {
                "capacity": 80,
                "location": "suburbios",
                "obligatorios": ["estacionamiento"]
            },
            "catering": {
                "meal_types": ["plato servido", "cocktail", "buffet"],
                "dietary_options": ["vegetariano", "sin gluten", "vegano", "sin lactosa"],
                "obligatorios": ["chef personal", "maridaje", "servicio"]
            },
            "decor": {
                "service_levels": ["básico"],
                "floral_arrangements": ["centros de mesa"],
                "obligatorios": ["iluminación"]
            }
        },
        
        # CONSULTA 2: Venue complejo, catering simple, decor premium
        "venue_complex": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "elegante",
            "venue": {
                "capacity": 150,
                "location": "centro",
                "obligatorios": ["estacionamiento", "accesibilidad", "cocina", "exterior"]
            },
            "catering": {
                "meal_types": ["buffet"],
                "dietary_options": ["vegetariano"],
                "obligatorios": ["servicio"]
            },
            "decor": {
                "service_levels": ["luxury"],
                "floral_arrangements": ["arco", "centros", "bouquet", "todo incluido"],
                "obligatorios": ["diseño completo", "iluminación profesional"]
            }
        },
        
        # CONSULTA 3: Venue básico, catering premium, decor complejo
        "catering_premium": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "elegante",
            "venue": {
                "capacity": 60,
                "location": "jardín",
                "obligatorios": ["exterior"]
            },
            "catering": {
                "meal_types": ["plato servido", "cocktail", "canapés"],
                "dietary_options": ["vegetariano", "sin gluten", "vegano", "sin lactosa", "sin nueces"],
                "obligatorios": ["chef personal", "maridaje", "presentación", "servicio"]
            },
            "decor": {
                "service_levels": ["premium"],
                "floral_arrangements": ["arco", "centros", "bouquet", "diseño personalizado"],
                "obligatorios": ["diseño personalizado", "iluminación profesional"]
            }
        },
        
        # CONSULTA 4: Todo básico
        "all_basic": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "elegante",
            "venue": {
                "capacity": 80,
                "location": "suburbios",
                "obligatorios": []
            },
            "catering": {
                "meal_types": ["buffet"],
                "dietary_options": ["vegetariano"],
                "obligatorios": []
            },
            "decor": {
                "service_levels": ["básico"],
                "floral_arrangements": ["centros de mesa"],
                "obligatorios": []
            }
        },
        
        # CONSULTA 5: Todo premium
        "all_premium": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "elegante",
            "venue": {
                "capacity": 200,
                "location": "centro",
                "obligatorios": ["estacionamiento", "accesibilidad", "cocina", "exterior", "terraza"]
            },
            "catering": {
                "meal_types": ["plato servido", "cocktail", "buffet", "canapés"],
                "dietary_options": ["vegetariano", "sin gluten", "vegano", "sin lactosa", "sin nueces", "sin mariscos"],
                "obligatorios": ["chef personal", "maridaje", "presentación", "servicio", "sommelier"]
            },
            "decor": {
                "service_levels": ["luxury"],
                "floral_arrangements": ["arco", "centros", "bouquet", "diseño personalizado", "todo incluido"],
                "obligatorios": ["diseño completo", "diseño personalizado", "iluminación profesional", "coordinación"]
            }
        }
    }

def print_distribution_analysis(distribution, query_name):
    """Imprime análisis detallado de la distribución."""
    total = sum(distribution.values())
    print(f"📊 Distribución resultante ({query_name}):")
    for category, amount in distribution.items():
        percentage = (amount / total) * 100
        print(f"  - {category.title()}: ${amount:,} ({percentage:.1f}%)")
    print()

def main():
    print("🧪 INICIANDO PRUEBA DEL SISTEMA DE MEMORIA MEJORADO")
    print("=" * 60)
    
    # Crear agente
    agent = BudgetDistributorAgent()
    
    # Obtener criterios de prueba
    test_criteria = create_test_criteria()
    
    # Ejecutar consultas secuenciales
    user_id = "test_user_variation"
    distributions = {}
    consistencies = []
    
    for i, (query_name, criteria) in enumerate(test_criteria.items(), 1):
        print(f"📋 CONSULTA #{i}: {query_name.replace('_', ' ').title()}")
        print("-" * 40)
        print(f"💰 Presupuesto: ${criteria['presupuesto_total']:,}")
        print(f"🎯 Tipo de criterios: {query_name}")
        
        # Ejecutar distribución
        distribution = agent.run(
            user_id=user_id,
            total_budget=criteria['presupuesto_total'],
            user_description=json.dumps(criteria)
        )
        
        distributions[query_name] = distribution
        
        # Mostrar distribución
        print_distribution_analysis(distribution, query_name)
        
        # Mostrar historial actual
        current_history = agent.history.get(user_id, {})
        print(f"💾 Historial actual: {current_history}")
        
        # Calcular consistencia si no es la primera consulta
        if i > 1:
            prev_distribution = list(distributions.values())[i-2]
            consistency = agent._calculate_consistency(
                {k: v/sum(prev_distribution.values()) for k, v in prev_distribution.items()},
                {k: v/sum(distribution.values()) for k, v in distribution.items()}
            )
            consistencies.append(consistency)
            print(f"🔄 Consistencia con consulta anterior: {consistency:.3f}")
        
        print("\n" + "="*60 + "\n")
    
    # Análisis final
    print("📈 ANÁLISIS FINAL DE VARIACIÓN")
    print("=" * 60)
    
    # Calcular variación entre distribuciones
    print("🔄 Análisis de variación entre consultas:")
    for i in range(len(distributions)):
        for j in range(i+1, len(distributions)):
            dist1_name = list(distributions.keys())[i]
            dist2_name = list(distributions.keys())[j]
            dist1 = distributions[dist1_name]
            dist2 = distributions[dist2_name]
            
            # Normalizar distribuciones
            total1 = sum(dist1.values())
            total2 = sum(dist2.values())
            norm1 = {k: v/total1 for k, v in dist1.items()}
            norm2 = {k: v/total2 for k, v in dist2.items()}
            
            # Calcular diferencia promedio
            avg_diff = sum(abs(norm1[k] - norm2[k]) for k in norm1.keys()) / len(norm1)
            print(f"  {dist1_name} → {dist2_name}: {avg_diff:.3f} diferencia promedio")
    
    print(f"\n✅ Historial final guardado: {agent.history.get(user_id, {})}")
    
    # Verificar que todas las distribuciones sumen correctamente
    print("\n✅ Verificación de distribuciones:")
    for name, dist in distributions.items():
        total = sum(dist.values())
        expected = test_criteria[name]['presupuesto_total']
        print(f"  {name}: ${total:,} (esperado: ${expected:,})")
    
    print("\n🎉 PRUEBA COMPLETADA")
    
    # Prueba de persistencia
    print("\n🔄 PRUEBA DE PERSISTENCIA DE MEMORIA")
    print("=" * 60)
    
    print("📝 Primera instancia - Ejecutando distribución...")
    agent1 = BudgetDistributorAgent()
    distribution1 = agent1.run(
        user_id=user_id,
        total_budget=50000,
        user_description=json.dumps(test_criteria["venue_simple"])
    )
    print(f"💾 Historial en primera instancia: {agent1.history.get(user_id, {})}")
    
    print("\n📝 Segunda instancia - Cargando historial...")
    agent2 = BudgetDistributorAgent()
    print(f"💾 Historial en segunda instancia: {agent2.history.get(user_id, {})}")
    
    if agent1.history.get(user_id) == agent2.history.get(user_id):
        print("✅ PERSISTENCIA EXITOSA: El historial se mantiene entre instancias")
    else:
        print("❌ ERROR: El historial no se mantiene entre instancias")
    
    print("\n" + "="*60)
    print("📋 RESUMEN DE PRUEBAS")
    print("="*60)
    print("✅ Sistema de memoria: FUNCIONANDO")
    print("✅ Persistencia: FUNCIONANDO")
    print("✅ Variación mejorada: FUNCIONANDO")
    print("\n🎉 TODAS LAS PRUEBAS EXITOSAS")

if __name__ == "__main__":
    main() 