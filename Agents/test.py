
# test/test_venue_agent_real.py
import sys
import os
import requests

# Añade la carpeta base del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Crawler.core import AdvancedCrawlerAgent
from Crawler.graph import KnowledgeGraphInterface
from Crawler.expert import ExpertSystemInterface
from venue_manager import VenueAgent
from Crawler.policy import CrawlPolicy

# 1. Inicialización de componentes
graph = KnowledgeGraphInterface("venues_graph.json")
graph.clean_errors()
expert = ExpertSystemInterface()
policy = CrawlPolicy()

crawler = AdvancedCrawlerAgent(
    name="TestCrawler",
    graph_interface=graph,
    expert_system=expert,
    policy=policy
)

agent = VenueAgent(
    name="VenueAgent",
    crawler=crawler,
    graph=graph,
    expert=expert
)

# 2. Criterios y URL de prueba
criteria = {
    "obligatorios": ["capacity", "price"],
    "capacity": 60,
    "price": 4000,
    "opcionales": ["venue_type", "atmosphere"],
    "venue_type": ["mansion", "country club"],
    "atmosphere": ["inside"]
}

urls = [
    "https://www.zola.com/wedding-vendors/search/wedding-venues?page=1"
]


# 3. Ejecutar búsqueda
venues = agent.find_venues(criteria, urls)
graph.save_to_file("venues_graph.json") 
graph.clean_errors()

print("\n✅ Venues encontrados:")
for v in venues:
    data = v.get("original_data", {})
    score = agent.score_optional(data, criteria)
    print(f"- {data.get('title')} | Capacidad: {data.get('capacity')} | Ciudad: {data.get('location') or data.get('city')} | Precio: {data.get('price')} | Score opcionales: {score}")



