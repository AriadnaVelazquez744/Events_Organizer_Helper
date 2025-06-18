#!/usr/bin/env python3
"""
Script de prueba para verificar las correcciones del flujo BDI
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.planner.Planneragent import PlannerAgentBDI, MessageBus
from agents.session_memory import SessionMemoryManager
from agents.budget.BudgetAgent import BudgetDistributorAgent
from agents.venue.venue_manager import VenueAgent
from agents.catering.catering_manager import CateringAgent
from agents.decor.decor_manager import DecorAgent
from crawler.core.core import AdvancedCrawlerAgent
from crawler.extraction.graph import KnowledgeGraphInterface
from crawler.extraction.expert import ExpertSystemInterface
from crawler.core.policy import CrawlPolicy

def setup_agents(bus):
    """Configura y registra todos los agentes necesarios en el bus."""
    # Inicializar componentes compartidos
    expert = ExpertSystemInterface()
    policy = CrawlPolicy()
    
    # Cargar grafos
    try:
        graph_v = KnowledgeGraphInterface("src/agents/venues/venues_graph.json")
        graph_v.clean_errors()
        print(f"[GRAPH] Grafo de venues cargado con {len(graph_v.nodes)} nodos")
    except Exception as e:
        print(f"[GRAPH] Error al cargar el grafo de venues: {str(e)}")
        graph_v = KnowledgeGraphInterface("venues_graph.json")
        graph_v.clean_errors()
        
    try:
        graph_c = KnowledgeGraphInterface("src/agents/catering/catering_graph.json")
        graph_c.clean_errors()
        print(f"[GRAPH] Grafo de catering cargado con {len(graph_c.nodes)} nodos")
    except Exception as e:
        print(f"[GRAPH] Error al cargar el grafo de catering: {str(e)}")
        graph_c = KnowledgeGraphInterface("catering_graph.json")
        graph_c.clean_errors()

    try:
        graph_d = KnowledgeGraphInterface("src/agents/decor/decor_graph.json")
        graph_d.clean_errors()
        print(f"[GRAPH] Grafo de decor cargado con {len(graph_d.nodes)} nodos")
    except Exception as e:
        print(f"[GRAPH] Error al cargar el grafo de decor: {str(e)}")
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
    budget_agent = BudgetDistributorAgent()
    
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
    
    print("✅ Agentes registrados en el MessageBus")
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

def test_corrected_flow():
    """Prueba el flujo corregido para verificar que no hay tareas duplicadas."""
    print("🧪 INICIANDO PRUEBA DEL FLUJO CORREGIDO")
    print("=" * 60)
    
    # Configurar el sistema
    bus = MessageBus()
    memory_manager = SessionMemoryManager()
    planner = PlannerAgentBDI("PlannerAgent", bus, memory_manager)
    
    # Configurar y registrar agentes
    agents = setup_agents(bus)
    
    # Iniciar el bus
    bus.start()
    
    # Crear sesión
    session_id = planner.create_session("test_user_corrected")
    print(f"📝 Sesión creada: {session_id}")
    
    # Crear petición de prueba
    request = {
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
    
    print(f"📋 Petición de prueba: {request}")
    
    # Procesar petición
    print("\n🔄 Ejecutando flujo corregido...")
    planner._handle_user_request(session_id, request)
    
    # Verificar desires creados
    desires = planner.desires.get(session_id, [])
    print(f"\n🎯 Desires creados: {len(desires)}")
    for desire in desires:
        print(f"  - {desire.type} (prioridad: {desire.priority})")
    
    # Verificar intentions creadas
    intentions = planner.intentions.get(session_id, [])
    print(f"\n📋 Intentions creadas: {len(intentions)}")
    for intention in intentions:
        print(f"  - Intention {intention.id[:8]}... para desire {intention.desire_id[:8]}...")
        print(f"    Tareas: {len(intention.tasks)}")
    
    # Verificar tareas iniciales (solo debería haber budget_distribution)
    initial_tasks = planner.task_queue.get(session_id, [])
    print(f"\n📝 Tareas iniciales: {len(initial_tasks)}")
    for task in initial_tasks:
        print(f"  - {task.type} (estado: {task.status})")
    
    # Verificar que solo hay una tarea (budget_distribution)
    if len(initial_tasks) == 1 and initial_tasks[0].type == "budget_distribution":
        print("✅ CORRECTO: Solo hay una tarea inicial (budget_distribution)")
    else:
        print("❌ ERROR: Debería haber solo una tarea inicial (budget_distribution)")
        return False
    
    # Simular la respuesta del BudgetDistributorAgent
    print("\n🔄 Simulando respuesta del BudgetDistributorAgent...")
    budget_response = {
        "origen": "BudgetDistributorAgent",
        "destino": "PlannerAgent",
        "tipo": "task_response",
        "contenido": {
            "task_id": initial_tasks[0].id,
            "distribution": {
                "venue": 27500,
                "catering": 15000,
                "decor": 7500
            }
        },
        "session_id": session_id
    }
    
    # Procesar la respuesta
    planner._handle_agent_response(session_id, budget_response)
    
    # Verificar tareas después de la distribución de presupuesto
    final_tasks = planner.task_queue.get(session_id, [])
    print(f"\n📝 Tareas después de distribución de presupuesto: {len(final_tasks)}")
    for task in final_tasks:
        print(f"  - {task.type} (estado: {task.status})")
        if hasattr(task, 'parameters') and 'budget' in task.parameters:
            print(f"    Presupuesto: ${task.parameters['budget']:,}")
    
    # Verificar que hay exactamente 3 tareas de búsqueda
    search_tasks = [t for t in final_tasks if t.type in ["venue_search", "catering_search", "decor_search"]]
    if len(search_tasks) == 3:
        print("✅ CORRECTO: Se crearon exactamente 3 tareas de búsqueda")
    else:
        print(f"❌ ERROR: Se esperaban 3 tareas de búsqueda, se encontraron {len(search_tasks)}")
        return False
    
    # Verificar que no hay tareas duplicadas
    task_types = [t.type for t in final_tasks]
    if len(task_types) == len(set(task_types)):
        print("✅ CORRECTO: No hay tareas duplicadas")
    else:
        print("❌ ERROR: Hay tareas duplicadas")
        return False
    
    print("\n🎉 PRUEBA EXITOSA: El flujo corregido funciona correctamente")
    return True

if __name__ == "__main__":
    try:
        success = test_corrected_flow()
        if success:
            print("\n✅ TODAS LAS CORRECCIONES FUNCIONAN CORRECTAMENTE")
        else:
            print("\n❌ HAY PROBLEMAS EN LAS CORRECCIONES")
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc() 