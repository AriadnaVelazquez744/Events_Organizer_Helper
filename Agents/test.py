
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
    "obligatorios": ["capacidad", "precio"],
    "precio": 60,
    "presupuesto": 4000,
    "opcionales": ["tipo_local", "ambiente"],
    "tipo_local": ["mansión", "country club"],
    "ambiente": ["interior"]
}

urls = [
    "https://www.zola.com/wedding-vendors/search/wedding-venues?page=1"
]


# 3. Ejecutar búsqueda
venues = agent.find_venues(criteria, urls)
graph.save_to_file("venues_graph.json") 

# 4. Ver resultados
print("\n✅ Venues encontrados:")
for v in venues:
    print(f"- {v.get('title')} | Capacidad: {v.get('capacidad')} | Ciudad: {v.get('ciudad')} | Precio: {v.get('precio')}")


# def obtener_venues_desde_api(ciudad="Seattle", capacidad=60, tipo_evento="wedding"):
#     url = "https://www.tagvenue.com/us/"
#     payload = {
#         "city": ciudad,
#         "people": capacidad,
#         "tags": [tipo_evento],
#         "iso_country_code": "US",  # o US si usas Seattle
#         "page": 1,
#         "items_per_page": 50
#     }
#     headers = {
#         "Content-Type": "application/json",
#         "Accept": "application/json",
#         "User-Agent": "Mozilla/5.0"
#     }

#     response = requests.post(url, json=payload, headers=headers)
#     if response.status_code == 200:
#         data = response.json()
#         venues = []
#         for item in data.get("rooms", []):
#             full_url = f"https://www.tagvenue.com{item.get('url')}"
#             venues.append(full_url)
#         return venues
#     else:
#         print("⚠️ Error al consultar la API:", response.status_code)
#         return []

# urls = obtener_venues_desde_api(ciudad="London", capacidad=50, tipo_evento="conference")
# print("🔗 URLs encontradas:")
# for u in urls:
#     print("-", u)
