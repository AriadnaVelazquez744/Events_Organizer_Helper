#!/usr/bin/env python3
"""
Análisis completo del sistema de planificación de eventos.
Verifica todos los componentes y identifica errores o componentes faltantes.
"""

import os
import sys
import json
import importlib
from typing import Dict, List, Any

def print_section(title: str):
    """Imprime una sección con formato."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def print_result(title: str, data: Any):
    """Imprime un resultado con formato."""
    print(f"\n{title}:")
    print("-" * 40)
    if isinstance(data, dict):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(data)
    print("-" * 40)

class SystemAnalyzer:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []
        
    def add_error(self, component: str, message: str):
        self.errors.append(f"[ERROR] {component}: {message}")
        
    def add_warning(self, component: str, message: str):
        self.warnings.append(f"[WARNING] {component}: {message}")
        
    def add_success(self, component: str, message: str):
        self.successes.append(f"[SUCCESS] {component}: {message}")

    def analyze_file_structure(self):
        """Analiza la estructura de archivos del sistema."""
        print_section("ANÁLISIS DE ESTRUCTURA DE ARCHIVOS")
        
        required_files = [
            "main.py",
            "Agents/Planneragent.py",
            "Agents/venue_manager.py",
            "Agents/catering_manager.py", 
            "Agents/decor_manager.py",
            "Agents/BudgetAgent.py",
            "Agents/session_memory.py",
            "Agents/beliefs_schema.py",
            "Crawler/core.py",
            "Crawler/graph.py",
            "Crawler/expert.py",
            "Crawler/policy.py",
            "Crawler/scrapper.py",
            "Crawler/quality_validator.py",
            "Crawler/enrichment_engine.py",
            "Crawler/monitoring.py",
            "Crawler/llm_extract_openrouter.py"
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
                self.add_error("File Structure", f"Archivo faltante: {file_path}")
            else:
                self.add_success("File Structure", f"Archivo presente: {file_path}")
        
        if missing_files:
            print_result("Archivos Faltantes", missing_files)
        else:
            print("✅ Todos los archivos requeridos están presentes")

    def analyze_imports(self):
        """Analiza las importaciones de los módulos principales."""
        print_section("ANÁLISIS DE IMPORTACIONES")
        
        modules_to_test = [
            ("main", "main"),
            ("Agents.Planneragent", "PlannerAgentBDI"),
            ("Agents.venue_manager", "VenueAgent"),
            ("Agents.catering_manager", "CateringAgent"),
            ("Agents.decor_manager", "DecorAgent"),
            ("Agents.BudgetAgent", "BudgetDistributorAgent"),
            ("Agents.session_memory", "SessionMemoryManager"),
            ("Crawler.core", "AdvancedCrawlerAgent"),
            ("Crawler.graph", "KnowledgeGraphInterface"),
            ("Crawler.quality_validator", "DataQualityValidator"),
            ("Crawler.enrichment_engine", "DynamicEnrichmentEngine"),
            ("Crawler.monitoring", "DataQualityMonitor")
        ]
        
        for module_name, class_name in modules_to_test:
            try:
                module = importlib.import_module(module_name)
                if hasattr(module, class_name):
                    self.add_success("Imports", f"✅ {module_name}.{class_name} importado correctamente")
                else:
                    self.add_error("Imports", f"❌ Clase {class_name} no encontrada en {module_name}")
            except ImportError as e:
                self.add_error("Imports", f"❌ Error importando {module_name}: {str(e)}")
            except Exception as e:
                self.add_warning("Imports", f"⚠️ Error inesperado en {module_name}: {str(e)}")

    def analyze_graph_files(self):
        """Analiza los archivos de grafos de conocimiento."""
        print_section("ANÁLISIS DE GRAFOS DE CONOCIMIENTO")
        
        graph_files = [
            "Agents/venues_graph.json",
            "Agents/catering_graph.json", 
            "Agents/decor_graph.json"
        ]
        
        for graph_file in graph_files:
            if os.path.exists(graph_file):
                try:
                    with open(graph_file, 'r') as f:
                        data = json.load(f)
                    size = os.path.getsize(graph_file)
                    self.add_success("Graph Files", f"✅ {graph_file}: {len(data)} nodos, {size/1024/1024:.1f}MB")
                except json.JSONDecodeError as e:
                    self.add_error("Graph Files", f"❌ {graph_file}: Error JSON - {str(e)}")
                except Exception as e:
                    self.add_error("Graph Files", f"❌ {graph_file}: Error - {str(e)}")
            else:
                self.add_warning("Graph Files", f"⚠️ {graph_file}: No encontrado")

    def analyze_rag_systems(self):
        """Analiza los sistemas RAG."""
        print_section("ANÁLISIS DE SISTEMAS RAG")
        
        rag_files = [
            "Agents/venue_rag.py",
            "Agents/catering_rag.py",
            "Agents/decor_rag.py",
            "Agents/planner_rag.py"
        ]
        
        for rag_file in rag_files:
            if os.path.exists(rag_file):
                try:
                    with open(rag_file, 'r') as f:
                        content = f.read()
                    
                    # Verificar que tenga las clases principales
                    if "class" in content and "def" in content:
                        self.add_success("RAG Systems", f"✅ {rag_file}: Estructura válida")
                    else:
                        self.add_warning("RAG Systems", f"⚠️ {rag_file}: Estructura sospechosa")
                except Exception as e:
                    self.add_error("RAG Systems", f"❌ {rag_file}: Error - {str(e)}")
            else:
                self.add_error("RAG Systems", f"❌ {rag_file}: No encontrado")

    def analyze_configuration(self):
        """Analiza la configuración del sistema."""
        print_section("ANÁLISIS DE CONFIGURACIÓN")
        
        # Verificar variables de entorno
        env_vars = ["OPENROUTER_API_KEY"]
        for var in env_vars:
            if os.getenv(var):
                self.add_success("Configuration", f"✅ Variable de entorno {var} configurada")
            else:
                self.add_warning("Configuration", f"⚠️ Variable de entorno {var} no configurada")
        
        # Verificar archivos de configuración
        config_files = ["requirements.txt", "pyproject.toml"]
        for config_file in config_files:
            if os.path.exists(config_file):
                self.add_success("Configuration", f"✅ {config_file} presente")
            else:
                self.add_warning("Configuration", f"⚠️ {config_file} no encontrado")

    def analyze_main_flow(self):
        """Analiza el flujo principal del sistema."""
        print_section("ANÁLISIS DEL FLUJO PRINCIPAL")
        
        try:
            # Intentar importar componentes principales
            from agents.planner.Planneragent import PlannerAgentBDI, MessageBus
            from agents.session_memory import SessionMemoryManager
            from crawler.quality.quality_validator import DataQualityValidator
            from crawler.quality.monitoring import DataQualityMonitor
            
            # Verificar que se pueden crear instancias
            bus = MessageBus()
            memory_manager = SessionMemoryManager()
            quality_validator = DataQualityValidator()
            quality_monitor = DataQualityMonitor(quality_validator)
            
            self.add_success("Main Flow", "✅ Componentes principales se pueden instanciar")
            
        except Exception as e:
            self.add_error("Main Flow", f"❌ Error en flujo principal: {str(e)}")

    def analyze_data_flow(self):
        """Analiza el flujo de datos entre componentes."""
        print_section("ANÁLISIS DEL FLUJO DE DATOS")
        
        # Verificar que los agentes pueden recibir mensajes
        try:
            from agents.venue.venue_manager import VenueAgent
            from agents.catering.catering_manager import CateringAgent
            from agents.decor.decor_manager import DecorAgent
            from agents.budget.BudgetAgent import BudgetDistributorAgent
            
            # Verificar que tienen método receive
            agents = [VenueAgent, CateringAgent, DecorAgent, BudgetDistributorAgent]
            for agent_class in agents:
                if hasattr(agent_class, 'receive'):
                    self.add_success("Data Flow", f"✅ {agent_class.__name__} tiene método receive")
                else:
                    self.add_error("Data Flow", f"❌ {agent_class.__name__} no tiene método receive")
                    
        except Exception as e:
            self.add_error("Data Flow", f"❌ Error verificando flujo de datos: {str(e)}")

    def analyze_enrichment_system(self):
        """Analiza el sistema de enriquecimiento."""
        print_section("ANÁLISIS DEL SISTEMA DE ENRIQUECIMIENTO")
        
        try:
            from crawler.quality.quality_validator import DataQualityValidator
            from crawler.quality.enrichment_engine import DynamicEnrichmentEngine
            
            validator = DataQualityValidator()
            engine = DynamicEnrichmentEngine(validator)
            
            # Verificar métodos críticos
            if hasattr(validator, 'validate_data_quality'):
                self.add_success("Enrichment", "✅ DataQualityValidator tiene método validate_data_quality")
            else:
                self.add_error("Enrichment", "❌ DataQualityValidator no tiene método validate_data_quality")
                
            if hasattr(engine, 'enrich_data'):
                self.add_success("Enrichment", "✅ DynamicEnrichmentEngine tiene método enrich_data")
            else:
                self.add_error("Enrichment", "❌ DynamicEnrichmentEngine no tiene método enrich_data")
                
        except Exception as e:
            self.add_error("Enrichment", f"❌ Error en sistema de enriquecimiento: {str(e)}")

    def generate_report(self):
        """Genera el reporte final."""
        print_section("REPORTE FINAL DEL ANÁLISIS")
        
        print(f"✅ Éxitos: {len(self.successes)}")
        print(f"⚠️ Advertencias: {len(self.warnings)}")
        print(f"❌ Errores: {len(self.errors)}")
        
        if self.errors:
            print_result("Errores Críticos", self.errors)
            
        if self.warnings:
            print_result("Advertencias", self.warnings)
            
        if self.successes:
            print_result("Componentes Funcionando", self.successes[:10])  # Solo mostrar primeros 10
            
        # Resumen
        total_components = len(self.successes) + len(self.warnings) + len(self.errors)
        if total_components > 0:
            success_rate = (len(self.successes) / total_components) * 100
            print(f"\n📊 Tasa de éxito: {success_rate:.1f}%")
            
            if success_rate >= 90:
                print("🎉 Sistema en excelente estado")
            elif success_rate >= 75:
                print("✅ Sistema en buen estado")
            elif success_rate >= 50:
                print("⚠️ Sistema necesita atención")
            else:
                print("❌ Sistema con problemas críticos")

def main():
    """Ejecuta el análisis completo del sistema."""
    analyzer = SystemAnalyzer()
    
    print_section("ANÁLISIS COMPLETO DEL SISTEMA DE PLANIFICACIÓN DE EVENTOS")
    
    # Ejecutar todos los análisis
    analyzer.analyze_file_structure()
    analyzer.analyze_imports()
    analyzer.analyze_graph_files()
    analyzer.analyze_rag_systems()
    analyzer.analyze_configuration()
    analyzer.analyze_main_flow()
    analyzer.analyze_data_flow()
    analyzer.analyze_enrichment_system()
    
    # Generar reporte final
    analyzer.generate_report()

if __name__ == "__main__":
    main() 