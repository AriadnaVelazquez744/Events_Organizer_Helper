
# test/test_real_crawler.py
from crawler.core.core import AdvancedCrawlerAgent
from crawler.extraction.graph import KnowledgeGraphInterface
from crawler.extraction.expert import ExpertSystemInterface
import time

def rule_detect_example_domain(knowledge):
    if "example" in knowledge["url"]:
        print(f"[RULE] 'example' domain detected: {knowledge['url']}")

def run_real_test():
    graph = KnowledgeGraphInterface()
    expert = ExpertSystemInterface()
    expert.add_rule(rule_detect_example_domain)

    agent = AdvancedCrawlerAgent("RealAgent", graph_interface=graph, expert_system=expert)

    urls = [
        "http://example.com",
        "https://www.iana.org/domains/reserved",
        "https://httpbin.org/html"
    ]

    for url in urls:
        print(f"\n>>> Crawling {url}")
        agent.crawl(url)
        time.sleep(1)  # evitar abuso o bloqueo

    print("\n=== Conocimiento extraído ===")
    for node in graph.nodes:
        print(f"- Título: {node['title']}")
        print(f"  URL: {node['url']}")
        print(f"  Entidades: {node['entities']}")
        print(f"  Timestamp: {node['timestamp']}")
        print("")

    # Persistencia
    graph.save_to_file("real_graph.json")
    print("[OK] Grafo guardado en 'real_graph.json'")

    # Carga para verificar
    loaded_graph = KnowledgeGraphInterface()
    loaded_graph.load_from_file("real_graph.json")
    assert len(loaded_graph.nodes) == len(graph.nodes), "Grafo cargado debe tener igual número de nodos"
    print("[OK] Grafo cargado correctamente")

if __name__ == "__main__":
    run_real_test()
