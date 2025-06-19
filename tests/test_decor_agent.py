# test/test_decor_agent.py
import sys
import os
import requests

# Añade la carpeta base del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler.core.core import AdvancedCrawlerAgent
from crawler.extraction.graph import KnowledgeGraphInterface
from crawler.extraction.expert import ExpertSystemInterface
from agents.decor.decor_manager import DecorAgent
from crawler.core.policy import CrawlPolicy

# 1. Inicialización de componentes
graph = KnowledgeGraphInterface("decor_graph.json")
graph.clean_errors()
expert = ExpertSystemInterface()
policy = CrawlPolicy()

crawler = AdvancedCrawlerAgent(
    name="TestCrawler",
    graph_interface=graph,
    expert_system=expert,
    policy=policy
)

agent = DecorAgent(
    name="DecorAgent",
    crawler=crawler,
    graph=graph,
    expert=expert
)

# 2. Criterios y URL de prueba
criteria = {
    "obligatorios": ["price", "service_levels", "floral_arrangements"],
    "price": 2000,
    "service_levels": ["Full-Service Floral Design"],
    "floral_arrangements": ["Bouquets", "Centerpieces", "Ceremony decor"],
    "opcionales": ["pre_wedding_services", "day_of_services", "arrangement_styles"],
    "pre_wedding_services": ["Consultations", "Event design", "Mock-ups"],
    "day_of_services": ["Delivery", "Setup"],
    "arrangement_styles": ["Flower-forward", "Foliage-centric"]
}

urls = [
    "https://www.zola.com/wedding-vendors/search/wedding-florists?page=1"
]

decor_nodes = graph.query("decor")

# Impresión del total
print(f"Total de floristas almacenados: {len(decor_nodes)}")

# 3. Ejecutar búsqueda
decors = agent.find_decor(criteria, urls)
graph.save_to_file("decor_graph.json") 
graph.clean_errors()

print("\n✅ Floristas encontrados:")
for d in decors:
    data = d.get("original_data", {})
    score = agent.score_optional(data, criteria)
    print(f"- {data.get('title')} | Ubicación: {data.get('ubication')} | Precio: {data.get('price')}")
    print(f"  Servicios: {data.get('service_levels')} | Arreglos: {data.get('floral_arrangements')}")
    print(f"  Score opcionales: {score}") 