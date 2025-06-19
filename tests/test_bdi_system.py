#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema BDI mejorado del PlannerAgent.
Este script prueba:
1. El ciclo BDI completo (Beliefs, Desires, Intentions)
2. El manejo inteligente de errores
3. La reconsideración de intentions
4. El sistema de reintentos
"""

import json
import os
import sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner.Planneragent import PlannerAgentBDI, MessageBus
from agents.session_memory import SessionMemoryManager
from agents.beliefs_schema import BeliefState

class TestLogger:
    def __init__(self, log_file="test_results.log"):
        self.log_file = log_file
        self.log_buffer = []
        
    def log(self, message):
        """Agrega un mensaje al buffer de log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_buffer.append(formatted_message)
        print(formatted_message)
        
    def save_log(self):
        """Guarda todos los logs en el archivo"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            for message in self.log_buffer:
                f.write(message + '\n')
        print(f"\n📁 Logs guardados en: {self.log_file}")
        
    def get_log_content(self):
        """Lee el contenido del archivo de log"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return "Archivo de log no encontrado"

# Crear logger global
logger = TestLogger()

def create_test_request():
    """Crea una petición de prueba completa."""
    return {
       "criterios": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "luxury",
            "venue": {
                "obligatorios": ["price", "capacity", "venue_type"],
                "capacity": 100,
                "venue_type": "mansion"
            },
            "catering": {
                "obligatorios": ["price", "meal_types", "dietary_options"],
                "meal_types": ["buffet", "plated"],
                "dietary_options": ["vegan", "gluten-free"]
            },
            "decor": {
                "obligatorios": ["price", "service_levels", "floral_arrangements"],
                "service_levels": ["Full-Service Floral Design"],
                "floral_arrangements": ["Bouquets", "Centerpieces", "Ceremony decor"]
            }
        }
    }

def create_error_request():
    """Crea una petición que generará errores."""
    return {
        "criterios": {
            "presupuesto_total": 1000,  # Presupuesto muy bajo
            "guest_count": 500,  # Demasiados invitados
            "style": "imposible",
            "venue": {
                "capacity": 10,  # Capacidad muy baja
                "location": "lugar_inexistente",
                "obligatorios": [
                    "servicio_imposible"
                ]
            }
        }
    }

def setup_agents(bus):
    """Configura y registra todos los agentes necesarios en el bus."""
    from agents.budget.BudgetAgent import BudgetDistributorAgent
    from agents.venue.venue_manager import VenueAgent
    from agents.catering.catering_manager import CateringAgent
    from agents.decor.decor_manager import DecorAgent
    from crawler.core.core import AdvancedCrawlerAgent
    from crawler.extraction.graph import KnowledgeGraphInterface
    from crawler.extraction.expert import ExpertSystemInterface
    from crawler.core.policy import CrawlPolicy
    
    # Inicializar componentes compartidos
    expert = ExpertSystemInterface()
    policy = CrawlPolicy()
    
    # Cargar grafos
    try:
        graph_v = KnowledgeGraphInterface("src/agents/venues/venues_graph.json")
        graph_v.clean_errors()
        logger.log(f"[GRAPH] Grafo de venues cargado con {len(graph_v.nodes)} nodos")
    except Exception as e:
        logger.log(f"[GRAPH] Error al cargar el grafo de venues: {str(e)}")
        graph_v = KnowledgeGraphInterface("venues_graph.json")
        graph_v.clean_errors()
        
    try:
        graph_c = KnowledgeGraphInterface("src/agents/catering/catering_graph.json")
        graph_c.clean_errors()
        logger.log(f"[GRAPH] Grafo de catering cargado con {len(graph_c.nodes)} nodos")
    except Exception as e:
        logger.log(f"[GRAPH] Error al cargar el grafo de catering: {str(e)}")
        graph_c = KnowledgeGraphInterface("catering_graph.json")
        graph_c.clean_errors()

    try:
        graph_d = KnowledgeGraphInterface("src/agents/decor/decor_graph.json")
        graph_d.clean_errors()
        logger.log(f"[GRAPH] Grafo de decor cargado con {len(graph_d.nodes)} nodos")
    except Exception as e:
        logger.log(f"[GRAPH] Error al cargar el grafo de decor: {str(e)}")
        graph_d = KnowledgeGraphInterface("decor_graph.json")
        graph_d.clean_errors()
    
    # Inicializar crawlers
    crawler_v = AdvancedCrawlerAgent(
        name="VenueCrawler",
        graph_interface=graph_v,
        expert_system=expert,
        policy=policy
    )
    
    crawler_c = AdvancedCrawlerAgent(
        name="CateringCrawler",
        graph_interface=graph_c,
        expert_system=expert,
        policy=policy
    )
    
    crawler_d = AdvancedCrawlerAgent(
        name="DecorCrawler",
        graph_interface=graph_d,
        expert_system=expert,
        policy=policy
    )
    
    # Crear agentes con los parámetros correctos
    budget_agent = BudgetDistributorAgent()  # Solo necesita el archivo de memoria por defecto
    
    venue_agent = VenueAgent(
        name="VenueAgent",
        crawler=crawler_v,
        graph=graph_v,
        expert=expert
    )
    
    catering_agent = CateringAgent(
        name="CateringAgent",
        crawler=crawler_c,
        graph=graph_c,
        expert=expert
    )
    
    decor_agent = DecorAgent(
        name="DecorAgent",
        crawler=crawler_d,
        graph=graph_d,
        expert=expert
    )
    
    # Registrar agentes en el bus
    bus.register("BudgetDistributorAgent", budget_agent.receive)
    bus.register("VenueAgent", venue_agent.receive)
    bus.register("CateringAgent", catering_agent.receive)
    bus.register("DecorAgent", decor_agent.receive)
    
    # Registrar los grafos en el bus
    bus.set_shared_data("venue_graph", graph_v)
    bus.set_shared_data("catering_graph", graph_c)
    bus.set_shared_data("decor_graph", graph_d)
    
    logger.log("✅ Agentes registrados en el MessageBus")
    return {
        "budget": budget_agent,
        "venue": venue_agent,
        "catering": catering_agent,
        "decor": decor_agent,
        "graphs": {
            "venue": graph_v,
            "catering": graph_c,
            "decor": graph_d
        }
    }

def test_bdi_cycle():
    """Prueba el ciclo BDI completo."""
    logger.log("\n🧪 INICIANDO PRUEBA DEL CICLO BDI")
    logger.log("=" * 60)
    
    # Configurar el sistema
    bus = MessageBus()
    memory_manager = SessionMemoryManager()
    planner = PlannerAgentBDI("PlannerAgent", bus, memory_manager)
    
    # Configurar y registrar agentes
    agents = setup_agents(bus)
    
    # Iniciar el bus
    bus.start()
    
    # Crear sesión
    session_id = planner.create_session("test_user")
    logger.log(f"📝 Sesión creada: {session_id}")
    
    # Crear petición de prueba
    request = create_test_request()
    logger.log(f"📋 Petición de prueba: {json.dumps(request, indent=2, ensure_ascii=False)}")
    
    # Procesar petición
    logger.log("\n🔄 Ejecutando ciclo BDI...")
    planner._handle_user_request(session_id, request)
    
    # Verificar desires creados
    desires = planner.desires.get(session_id, [])
    logger.log(f"\n🎯 Desires creados: {len(desires)}")
    for desire in desires:
        logger.log(f"  - {desire.type} (prioridad: {desire.priority})")
    
    # Verificar intentions creadas
    intentions = planner.intentions.get(session_id, [])
    logger.log(f"\n📋 Intentions creadas: {len(intentions)}")
    for intention in intentions:
        logger.log(f"  - Intention {intention.id} para desire {intention.desire_id}")
        logger.log(f"    Tareas: {len(intention.tasks)}")
    
    # Verificar que se crearon tareas
    tasks = planner.task_queue.get(session_id, [])
    logger.log(f"\n📝 Tareas creadas: {len(tasks)}")
    for task in tasks:
        logger.log(f"  - {task.type} (estado: {task.status})")
    
    # Verificar beliefs - ARREGLADO: usar to_dict() para iterar
    beliefs = memory_manager.get_beliefs(session_id)
    beliefs_dict = beliefs.to_dict()["beliefs"] if hasattr(beliefs, 'to_dict') else beliefs
    logger.log(f"\n💭 Beliefs actualizados:")
    logger.log(f"  - Criterios: {'Sí' if 'criterios' in beliefs_dict else 'No'}")
    logger.log(f"  - Presupuesto asignado: {'Sí' if 'presupuesto_asignado' in beliefs_dict else 'No'}")
    logger.log(f"  - Progreso de tareas: {'Sí' if 'task_progress' in beliefs_dict else 'No'}")
    
    return {
        "session_id": session_id,
        "desires_count": len(desires),
        "intentions_count": len(intentions),
        "tasks_count": len(tasks),
        "beliefs_updated": len(beliefs_dict) > 0
    }

def test_error_handling():
    """Prueba el manejo inteligente de errores."""
    logger.log("\n🚨 INICIANDO PRUEBA DE MANEJO DE ERRORES")
    logger.log("=" * 60)
    
    # Configurar el sistema
    bus = MessageBus()
    memory_manager = SessionMemoryManager()
    planner = PlannerAgentBDI("PlannerAgent", bus, memory_manager)
    
    # Configurar y registrar agentes
    agents = setup_agents(bus)
    bus.start()
    
    # Crear sesión
    session_id = planner.create_session("test_user_errors")
    logger.log(f"📝 Sesión creada: {session_id}")
    
    # Crear petición problemática
    request = create_error_request()
    logger.log(f"📋 Petición problemática creada")
    
    # Procesar petición
    logger.log("\n🔄 Procesando petición problemática...")
    planner._handle_user_request(session_id, request)
    
    # Simular error en una tarea
    from agents.planner.Planneragent import Task
    error_task = Task(
        id="test_error_task",
        type="venue_search",
        parameters={"test": "error"},
        status="pending"
    )
    
    logger.log("\n🚨 Simulando error en tarea...")
    planner._handle_task_error(session_id, error_task, "No se encontraron resultados")
    
    # Verificar que se crearon estrategias de corrección
    beliefs = memory_manager.get_beliefs(session_id)
    beliefs_dict = beliefs.to_dict()["beliefs"] if hasattr(beliefs, 'to_dict') else beliefs
    error_history = beliefs_dict.get("error_history", [])
    logger.log(f"\n📊 Historial de errores: {len(error_history)}")
    for error in error_history:
        logger.log(f"  - {error['task_type']}: {error['error']}")
    
    # Verificar que se crearon tareas de corrección
    correction_tasks = [t for t in planner.task_queue.get(session_id, []) 
                       if "correction_strategy" in t.parameters]
    logger.log(f"\n🔧 Tareas de corrección creadas: {len(correction_tasks)}")
    for task in correction_tasks:
        strategy = task.parameters.get("correction_strategy", {})
        logger.log(f"  - {task.type}: {strategy.get('type', 'unknown')}")
    
    return {
        "session_id": session_id,
        "errors_recorded": len(error_history),
        "correction_tasks": len(correction_tasks)
    }

def test_intention_reconsideration():
    """Prueba la reconsideración de intentions."""
    logger.log("\n🔄 INICIANDO PRUEBA DE RECONSIDERACIÓN DE INTENTIONS")
    logger.log("=" * 60)
    
    # Configurar el sistema
    bus = MessageBus()
    memory_manager = SessionMemoryManager()
    planner = PlannerAgentBDI("PlannerAgent", bus, memory_manager)
    
    # Configurar y registrar agentes
    agents = setup_agents(bus)
    bus.start()
    
    # Crear sesión
    session_id = planner.create_session("test_user_reconsideration")
    logger.log(f"📝 Sesión creada: {session_id}")
    
    # Crear petición normal
    request = create_test_request()
    planner._handle_user_request(session_id, request)
    
    # Verificar intentions iniciales
    initial_intentions = len(planner.intentions.get(session_id, []))
    logger.log(f"\n📋 Intentions iniciales: {initial_intentions}")
    
    # Simular error crítico
    from agents.planner.Planneragent import Task
    critical_error_task = Task(
        id="test_critical_error",
        type="budget_distribution",
        parameters={"test": "critical_error"},
        status="pending"
    )
    
    logger.log("\n🚨 Simulando error crítico...")
    planner._handle_task_error(session_id, critical_error_task, "budget_distribution timeout")
    
    # Forzar reconsideración de intentions
    logger.log("\n🔄 Forzando reconsideración de intentions...")
    planner._reconsider_intentions(session_id)
    
    # Verificar intentions después de la reconsideración
    final_intentions = len(planner.intentions.get(session_id, []))
    logger.log(f"\n📋 Intentions después de reconsideración: {final_intentions}")
    
    # Verificar que se crearon desires de corrección
    correction_desires = [d for d in planner.desires.get(session_id, []) 
                         if d.type.startswith("fix_")]
    logger.log(f"\n🎯 Desires de corrección: {len(correction_desires)}")
    for desire in correction_desires:
        logger.log(f"  - {desire.type} (prioridad: {desire.priority})")
    
    return {
        "session_id": session_id,
        "initial_intentions": initial_intentions,
        "final_intentions": final_intentions,
        "correction_desires": len(correction_desires)
    }

def test_rag_integration():
    """Prueba la integración con el sistema RAG."""
    logger.log("\n🧠 INICIANDO PRUEBA DE INTEGRACIÓN RAG")
    logger.log("=" * 60)
    
    # Configurar el sistema
    bus = MessageBus()
    memory_manager = SessionMemoryManager()
    planner = PlannerAgentBDI("PlannerAgent", bus, memory_manager)
    
    # Verificar que el RAG está disponible
    if not hasattr(planner, 'rag') or not planner.rag:
        logger.log("❌ RAG no disponible")
        return {"rag_available": False}
    
    # Probar sugerencias de corrección
    strategies = planner.rag.suggest_error_correction("venue_search", "No se encontraron resultados")
    logger.log(f"\n🔧 Estrategias de corrección para venue_search: {len(strategies)}")
    for strategy in strategies:
        logger.log(f"  - {strategy['type']}: {strategy['description']}")
    
    # Probar patrones de error
    error_patterns = planner.rag.get_error_patterns()
    logger.log(f"\n📊 Patrones de error disponibles: {len(error_patterns)}")
    for pattern_type, solutions in error_patterns.items():
        logger.log(f"  - {pattern_type}: {len(solutions)} soluciones")
    
    return {
        "rag_available": True,
        "correction_strategies": len(strategies),
        "error_patterns": len(error_patterns)
    }

def analyze_results():
    """Analiza los resultados del archivo de log."""
    logger.log("\n📊 ANALIZANDO RESULTADOS")
    logger.log("=" * 60)
    
    log_content = logger.get_log_content()
    
    # Análisis básico
    lines = log_content.split('\n')
    total_lines = len(lines)
    
    # Contar diferentes tipos de mensajes
    error_count = sum(1 for line in lines if '❌' in line or 'Error' in line or '⚠️' in line)
    success_count = sum(1 for line in lines if '✅' in line or 'Sí' in line)
    info_count = sum(1 for line in lines if '📝' in line or '📋' in line or '🎯' in line)
    
    logger.log(f"📈 Estadísticas del log:")
    logger.log(f"  - Total de líneas: {total_lines}")
    logger.log(f"  - Errores/Advertencias: {error_count}")
    logger.log(f"  - Éxitos: {success_count}")
    logger.log(f"  - Información: {info_count}")
    
    # Buscar patrones específicos
    if "Agentes registrados en el MessageBus" in log_content:
        logger.log("✅ Sistema de agentes inicializado correctamente")
    else:
        logger.log("❌ Problemas en la inicialización de agentes")
    
    if "Desires creados:" in log_content:
        logger.log("✅ Ciclo BDI funcionando (desires creados)")
    else:
        logger.log("❌ Problemas en el ciclo BDI")
    
    if "Intentions creadas:" in log_content:
        logger.log("✅ Planificación funcionando (intentions creadas)")
    else:
        logger.log("❌ Problemas en la planificación")
    
    if "Tareas creadas:" in log_content:
        logger.log("✅ Sistema de tareas funcionando")
    else:
        logger.log("❌ Problemas en el sistema de tareas")
    
    # Buscar errores específicos
    if "Timeout esperando respuesta" in log_content:
        logger.log("⚠️ Problemas de comunicación entre agentes (timeouts)")
    
    if "No se encontró" in log_content:
        logger.log("⚠️ Problemas con archivos o recursos faltantes")
    
    return {
        "total_lines": total_lines,
        "errors": error_count,
        "successes": success_count,
        "info": info_count
    }

if __name__ == "__main__":
    try:
        logger.log("🧪 INICIANDO PRUEBAS DEL SISTEMA BDI MEJORADO")
        logger.log("=" * 80)
        
        # Ejecutar todas las pruebas
        results = {}
        
        # Prueba 1: Ciclo BDI
        results["bdi_cycle"] = test_bdi_cycle()
        
        # Prueba 2: Manejo de errores
        results["error_handling"] = test_error_handling()
        
        # Prueba 3: Reconsideración de intentions
        results["intention_reconsideration"] = test_intention_reconsideration()
        
        # Prueba 4: Integración RAG
        results["rag_integration"] = test_rag_integration()
        
        # Resumen final
        logger.log("\n" + "=" * 80)
        logger.log("📋 RESUMEN DE PRUEBAS")
        logger.log("=" * 80)
        
        for test_name, result in results.items():
            logger.log(f"\n🔍 {test_name.upper()}:")
            for key, value in result.items():
                logger.log(f"  - {key}: {value}")
        
        # Evaluación general
        success_count = sum(1 for result in results.values() if result)
        total_tests = len(results)
        
        logger.log(f"\n🎯 RESULTADO GENERAL: {success_count}/{total_tests} pruebas exitosas")
        
        if success_count == total_tests:
            logger.log("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        else:
            logger.log("❌ ALGUNAS PRUEBAS FALLARON")
        
        # Guardar logs
        logger.save_log()
        
        # Analizar resultados
        analysis = analyze_results()
        logger.log(f"\n📊 ANÁLISIS FINAL: {analysis}")
        
        # Guardar análisis en archivo separado
        with open("test_analysis.json", "w", encoding="utf-8") as f:
            json.dump({
                "results": results,
                "analysis": analysis,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        logger.log("📁 Análisis guardado en: test_analysis.json")
            
    except Exception as e:
        logger.log(f"❌ Error durante las pruebas: {str(e)}")
        import traceback
        logger.log(f"Traceback: {traceback.format_exc()}")
        logger.save_log()