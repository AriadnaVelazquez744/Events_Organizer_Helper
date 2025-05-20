
# test/test_venue_agent_real.py
import sys
import os

# Añade la carpeta base del proyecto al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Crawler.core import AdvancedCrawlerAgent
from Crawler.graph import KnowledgeGraphInterface
from Crawler.expert import ExpertSystemInterface
from venue_manager import VenueAgent
from Crawler.policy import CrawlPolicy

# 1. Inicialización de componentes
graph = KnowledgeGraphInterface()
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
    "capacidad": 70,
    "presupuesto": 10000,
    "ciudad": "London"
}

urls = [
    "https://www.tagvenue.com/rooms/london/17182/the-penthouse-at-no-4-hamilton-place",
    "https://www.tagvenue.com/rooms/london/2013/the-long-room-at-the-anthologist",
    "https://www.tagvenue.com/rooms/london/12652/the-rooftop-at-big-easy-canary-wharf"
]


# 3. Ejecutar búsqueda
venues = agent.find_venues(criteria, urls)

# 4. Ver resultados
print("\n✅ Venues encontrados:")
for v in venues:
    print(f"- {v.get('title')} | Capacidad: {v.get('capacidad')} | Ciudad: {v.get('ciudad')} | Precio: {v.get('precio')}")
