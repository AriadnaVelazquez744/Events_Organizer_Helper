#!/usr/bin/env python3
"""
Script para enriquecer retroactivamente todos los datos existentes en el grafo
que tengan baja calidad de datos.
"""

import json
import os
from Crawler.quality_validator import DataQualityValidator
from Crawler.enrichment_engine import DynamicEnrichmentEngine
from Crawler.graph import KnowledgeGraphInterface

def enrich_existing_data():
    """Enriquece todos los datos existentes en el grafo que necesiten mejora."""
    print("=== ENRIQUECIMIENTO RETROACTIVO DE DATOS ===")
    
    # Inicializar componentes
    validator = DataQualityValidator()
    enrichment_engine = DynamicEnrichmentEngine(validator)
    
    # Cargar grafos existentes
    graphs = {
        "venue": "Agents/venues_graph.json",
        "catering": "Agents/catering_graph.json", 
        "decor": "Agents/decor_graph.json"
    }
    
    total_enriched = 0
    total_processed = 0
    
    for graph_type, graph_file in graphs.items():
        if not os.path.exists(graph_file):
            print(f"[ENRICHMENT] Grafo {graph_file} no existe, saltando...")
            continue
            
        print(f"\n--- Procesando grafo: {graph_type} ---")
        
        # Cargar grafo
        graph = KnowledgeGraphInterface(graph_file)
        nodes = graph.nodes
        
        print(f"[ENRICHMENT] Nodos encontrados: {len(nodes)}")
        
        enriched_count = 0
        processed_count = 0
        skipped_count = 0
        
        for node_id, node_data in nodes.items():
            # Solo procesar nodos del tipo correcto
            if node_data.get("tipo") != graph_type:
                continue
                
            processed_count += 1
            
            # Verificar si el nodo tiene información mínima útil
            title = node_data.get("title", "")
            url = node_data.get("url", "")
            
            # Saltar nodos sin información útil
            if not title or title in ["Unknown", "Sin título", ""] or not url:
                #print(f"[ENRICHMENT] ⏭️ Saltando nodo sin información útil: {title}")
                skipped_count += 1
                continue
            
            # Validar calidad
            quality_result = validator.validate_data_quality(node_data, graph_type)
            score = quality_result["overall_score"]
            
            # Solo enriquecer si realmente necesita mejora y tiene información útil
            if score < 0.5 and quality_result["needs_enrichment"] and len(quality_result["missing_fields"]) > 0:
                print(f"[ENRICHMENT] Enriqueciendo '{title}' (score: {score:.2f}, faltantes: {quality_result['missing_fields']})")
                
                try:
                    # Aplicar enriquecimiento
                    enriched_data = enrichment_engine.enrich_data(node_data, graph_type)
                    
                    # Verificar si hubo mejora real
                    final_quality = validator.validate_data_quality(enriched_data, graph_type)
                    final_score = final_quality["overall_score"]
                    
                    # Solo actualizar si hay mejora significativa
                    if final_score > score + 0.1:  # Al menos 10% de mejora
                        # Actualizar el nodo en el grafo
                        graph.nodes[node_id] = enriched_data
                        enriched_count += 1
                        
                        print(f"[ENRICHMENT] ✅ Mejorado: {score:.2f} → {final_score:.2f}")
                    else:
                        print(f"[ENRICHMENT] ⚠️ Mejora insuficiente: {score:.2f} → {final_score:.2f}")
                        
                except Exception as e:
                    print(f"[ENRICHMENT] ❌ Error enriqueciendo '{title}': {str(e)}")
            else:
                if score >= 0.5:
                    print(f"[ENRICHMENT] ✅ '{title}' ya tiene buena calidad (score: {score:.2f})")
                else:
                    print(f"[ENRICHMENT] ⏭️ '{title}' no necesita enriquecimiento (score: {score:.2f})")
        
        # Guardar grafo actualizado solo si hubo cambios
        if enriched_count > 0:
            graph.save_to_file(graph_file)
            print(f"[ENRICHMENT] Grafo {graph_type} guardado con {enriched_count} nodos enriquecidos")
        else:
            print(f"[ENRICHMENT] No se requirieron cambios en el grafo {graph_type}")
        
        total_enriched += enriched_count
        total_processed += processed_count
        
        print(f"[ENRICHMENT] Resumen {graph_type}: {enriched_count}/{processed_count} nodos enriquecidos, {skipped_count} saltados")
    
    print(f"\n=== RESUMEN FINAL ===")
    print(f"Total procesados: {total_processed}")
    print(f"Total enriquecidos: {total_enriched}")
    print(f"Tasa de enriquecimiento: {(total_enriched/total_processed*100):.1f}%" if total_processed > 0 else "0%")

def analyze_quality_distribution():
    """Analiza la distribución de calidad de los datos existentes."""
    print("=== ANÁLISIS DE DISTRIBUCIÓN DE CALIDAD ===\n")
    
    validator = DataQualityValidator()
    
    # Cargar grafos existentes
    graphs = {
        "venue": "Agents/venues_graph.json",
        "catering": "Agents/catering_graph.json", 
        "decor": "Agents/decor_graph.json"
    }
    
    for graph_type, graph_file in graphs.items():
        print(f"--- Análisis: {graph_type} ---")
        
        if not os.path.exists(graph_file):
            print(f"[GRAPH] Grafo {graph_file} no existe")
            continue
            
        try:
            graph = KnowledgeGraphInterface(graph_file)
            nodes = graph.nodes
            
            # Solo considerar nodos del tipo correcto
            relevant_nodes = [
                node for node in nodes.values()
                if node.get("tipo") == graph_type
            ]
            
            if not relevant_nodes:
                print(f"[GRAPH] Grafo cargado desde {graph_file}")
                print(f"Nodos analizados: 0")
                print(f"Score promedio: 0.000")
                print(f"Distribución:")
                print(f"  - excellent: 0 (0.0%)")
                print(f"  - good: 0 (0.0%)")
                print(f"  - fair: 0 (0.0%)")
                print(f"  - poor: 0 (0.0%)")
                continue
            
            # Calcular scores
            scores = []
            distribution = {"excellent": 0, "good": 0, "fair": 0, "poor": 0}
            
            for node in relevant_nodes:
                quality_result = validator.validate_data_quality(node, graph_type)
                score = quality_result["overall_score"]
                scores.append(score)
                
                # Categorizar
                if score >= 0.8:
                    distribution["excellent"] += 1
                elif score >= 0.6:
                    distribution["good"] += 1
                elif score >= 0.4:
                    distribution["fair"] += 1
                else:
                    distribution["poor"] += 1
            
            # Calcular estadísticas
            avg_score = sum(scores) / len(scores) if scores else 0
            total_nodes = len(relevant_nodes)
            
            print(f"[GRAPH] Grafo cargado desde {graph_file}")
            print(f"Nodos analizados: {total_nodes}")
            print(f"Score promedio: {avg_score:.3f}")
            print(f"Distribución:")
            for category, count in distribution.items():
                percentage = (count / total_nodes * 100) if total_nodes > 0 else 0
                print(f"  - {category}: {count} ({percentage:.1f}%)")
                
        except Exception as e:
            print(f"[GRAPH] Error analizando {graph_file}: {str(e)}")
        
        print()

if __name__ == "__main__":
    # Primero analizar la distribución actual
    analyze_quality_distribution()
    
    # Luego aplicar enriquecimiento
    enrich_existing_data()
    
    # Finalmente analizar la distribución después del enriquecimiento
    print("\n" + "="*80)
    print("ANÁLISIS POST-ENRIQUECIMIENTO")
    print("="*80)
    analyze_quality_distribution()
    
    print("\n=== ENRIQUECIMIENTO COMPLETADO ===") 