
# test/test_venue_agent_real.py
import sys
import os
import requests

# Añade la carpeta base del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Crawler.core import AdvancedCrawlerAgent
from Crawler.graph import KnowledgeGraphInterface
from Crawler.expert import ExpertSystemInterface
from catering_manager import CateringAgent
from Crawler.policy import CrawlPolicy

# 1. Inicialización de componentes
graph = KnowledgeGraphInterface("catering_graph.json")
expert = ExpertSystemInterface()
policy = CrawlPolicy()

crawler = AdvancedCrawlerAgent(
    name="TestCrawler",
    graph_interface=graph,
    expert_system=expert,
    policy=policy
)

agent = CateringAgent(
    name="CateringAgent",
    crawler=crawler,
    graph=graph,
    expert=expert
)

# 2. Criterios y URL de prueba
criteria = {
    "obligatorios": ["capacidad", "precio"],
    "capacidad": 60,
    "precio": 4000,
    "opcionales": ["tipo_local", "ambiente"],
    "tipo_local": ["mansions", "country club"],
    "ambiente": ["interior"]
}

urls = [
    "https://www.theknot.com/marketplace/wedding-reception-venues-new-york-ny?sort=featured"
]


# 3. Ejecutar búsqueda
venues = agent.find_venues(criteria, urls)
graph.save_to_file("catering_graph.json") 

print("\n✅ Venues encontrados:")
for v in venues:
    data = v.get("original_data", {})
    score = agent.score_optional(data, criteria)
    print(f"- {data.get('title')} | Capacidad: {data.get('capacidad')} | Ciudad: {data.get('ubicacion') or data.get('ciudad')} | Precio: {data.get('precio')} | Score opcionales: {score}")



