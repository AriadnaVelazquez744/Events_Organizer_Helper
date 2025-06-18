
# test/test_venue_agent_real.py
import sys
import os
import requests

# Añade la carpeta base del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from crawler.core.core import AdvancedCrawlerAgent
from crawler.extraction.graph import KnowledgeGraphInterface
from crawler.extraction.expert import ExpertSystemInterface
from agents.catering.catering_manager import CateringAgent
from crawler.core.policy import CrawlPolicy

# 1. Inicialización de componentes
graph = KnowledgeGraphInterface("catering_graph.json")
graph.clean_errors()
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
    "obligatorios": ["price", "meal_types", "dietary_options"],
    "price": 4000,
    "meal_types": ["buffet", "plated"],
    "dietary_options": ["vegan", "gluten-free"],
    "opcionales": ["cuisines", "beverage_services"],
    "cuisines": ["italian", "mediterranean"],
    "beverage_services": ["bar", "open bar"]
    
}

urls = [
    "https://www.zola.com/wedding-vendors/search/wedding-catering?page=1"
]

venue_nodes = graph.query("catering")

# Impresión del total
print(f"Total de caterings almacenados: {len(venue_nodes)}")
# 3. Ejecutar búsqueda
caterings = agent.find_catering(criteria, urls)
graph.save_to_file("catering_graph.json") 
graph.clean_errors()

print("\n✅ Caterings encontrados:")
for c in caterings:
    data = c.get("original_data", {})
    score = agent.score_optional(data, criteria)
    print(f"- {data.get('title')} | Ubicación: {data.get('ubication')} | Precio: {data.get('price')} | Tipos comida: {data.get('meal_types')} | Score opcionales: {score}")


