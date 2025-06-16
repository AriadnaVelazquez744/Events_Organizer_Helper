from Agents.Planneragent import PlannerAgentBDI, MessageBus
from Agents.decor_manager import DecorAgent
from Agents.catering_manager import CateringAgent
from Agents.venue_manager import VenueAgent
from Crawler.core import AdvancedCrawlerAgent
from Crawler.graph import KnowledgeGraphInterface
from Crawler.expert import ExpertSystemInterface
from Crawler.policy import CrawlPolicy
from Agents.session_memory import SessionMemoryManager
from Agents.BudgetAgent import BudgetDistributorAgent
import json
from datetime import datetime

def print_section(title: str):
    """Imprime una sección con formato."""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80 + "\n")

def print_result(title: str, data: dict):
    """Imprime un resultado con formato."""
    print(f"\n{title}:")
    print("-" * 40)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("-" * 40)

def initialize_system():
    print_section("INICIALIZANDO SISTEMA")
    
    # Inicializar componentes compartidos
    print("Inicializando componentes compartidos...")
    
    # Intentar cargar los grafos existentes
    try:
        print("Intentando cargar grafos existentes...")
        graph_v = KnowledgeGraphInterface("/home/lia/Escritorio/Proyectos/Simulación/Event Plan/Events_Organizer_Helper/Agents/venues_graph.json")
        graph_v.clean_errors()
        print(f"[GRAPH] Grafo de venues cargado con {len(graph_v.nodes)} nodos")
    except Exception as e:
        print(f"[GRAPH] Error al cargar el grafo de venues: {str(e)}")
        print("[GRAPH] Creando nuevo grafo de venues...")
        graph_v = KnowledgeGraphInterface("venues_graph.json")
        graph_v.clean_errors()
        
    try:
        graph_c = KnowledgeGraphInterface("/home/lia/Escritorio/Proyectos/Simulación/Event Plan/Events_Organizer_Helper/Agents/catering_graph.json")
        graph_c.clean_errors()
        print(f"[GRAPH] Grafo de catering cargado con {len(graph_c.nodes)} nodos")
    except Exception as e:
        print(f"[GRAPH] Error al cargar el grafo de catering: {str(e)}")
        print("[GRAPH] Creando nuevo grafo de catering...")
        graph_c = KnowledgeGraphInterface("catering_graph.json")
        graph_c.clean_errors()

    try:
        graph_d = KnowledgeGraphInterface("/home/lia/Escritorio/Proyectos/Simulación/Event Plan/Events_Organizer_Helper/Agents/decor_graph.json")
        graph_d.clean_errors()
        print(f"[GRAPH] Grafo de decor cargado con {len(graph_d.nodes)} nodos")
    except Exception as e:
        print(f"[GRAPH] Error al cargar el grafo de decor: {str(e)}")
        print("[GRAPH] Creando nuevo grafo de decor...")
        graph_d = KnowledgeGraphInterface("decor_graph.json")
        graph_d.clean_errors()
    
    expert = ExpertSystemInterface()
    policy = CrawlPolicy()
    memory_manager = SessionMemoryManager()
    bus = MessageBus()

    # Registrar los grafos en el bus
    bus.set_shared_data("venue_graph", graph_v)
    bus.set_shared_data("catering_graph", graph_c)
    bus.set_shared_data("decor_graph", graph_d)

    # Inicializar crawlers específicos para cada tipo
    print("Inicializando crawlers...")
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

    # Inicializar agentes
    print("Inicializando agentes especializados...")
    decor_agent = DecorAgent(
        name="DecorAgent",
        crawler=crawler_d,
        graph=graph_d,
        expert=expert
    )

    catering_agent = CateringAgent(
        name="CateringAgent",
        crawler=crawler_c,
        graph=graph_c,
        expert=expert
    )

    venue_agent = VenueAgent(
        name="VenueAgent",
        crawler=crawler_v,
        graph=graph_v,
        expert=expert
    )

    planner = PlannerAgentBDI(
        name="PlannerAgent",
        bus=bus,
        memory_manager=memory_manager
    )

    budget_agent = BudgetDistributorAgent()

    # Registrar agentes en el bus
    print("Registrando agentes en el bus de mensajes...")
    bus.register("PlannerAgent", planner.receive)
    bus.register("VenueAgent", venue_agent.receive)
    bus.register("CateringAgent", catering_agent.receive)
    bus.register("DecorAgent", decor_agent.receive)
    bus.register("BudgetDistributorAgent", budget_agent.receive)

    # Iniciar el bus de mensajes
    print("Iniciando bus de mensajes...")
    bus.start()

    print("\n✅ Sistema inicializado correctamente")
    return {
        "planner": planner,
        "bus": bus,
        "graphs": {
            "venue": graph_v,
            "catering": graph_c,
            "decor": graph_d
        },
        "memory": memory_manager
    }

def main():
    # Inicializar el sistema
    system = initialize_system()
    planner = system["planner"]
    
    print_section("CREANDO SESIÓN")
    # Ejemplo de uso
    session_id = planner.create_session("user_1")
    print(f"Sesión creada con ID: {session_id}")
    
    print_section("ENVIANDO PETICIÓN")
    # Ejemplo de petición
    request = {
        "criterios": {
            "presupuesto_total": 50000,
            "guest_count": 100,
            "style": "classic",
            "venue": {
                "obligatorios": ["price", "capacity", "location"],
                "capacity": 100,
                "location": "Los Angeles"
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
    
    print("Petición a procesar:")
    print(json.dumps(request, indent=2, ensure_ascii=False))
    
    print_section("PROCESANDO PETICIÓN")
    # Enviar petición al planner
    response = planner.receive({
        "origen": "user",
        "destino": "PlannerAgent",
        "tipo": "user_request",
        "contenido": request,
        "session_id": session_id
    })
    
    print_section("RESULTADOS")
    if response:
        print_result("Respuesta del sistema", response)
    else:
        print("❌ No se recibió respuesta del sistema")
    
    print_section("ESTADO FINAL")
    # Obtener estado final de la sesión
    session_info = system["memory"].get_session_info(session_id)
    print_result("Información de la sesión", session_info)
    
    # Obtener beliefs finales
    beliefs = system["memory"].get_beliefs(session_id)
    print_result("Estado de creencias", beliefs.resumen())

if __name__ == "__main__":
    main()
