
# crawler/manager.py
from typing import List
from src.crawler.core.core import AdvancedCrawlerAgent

class CrawlerManager:
    def __init__(self, agents: List[AdvancedCrawlerAgent]):
        self.agents = agents

    def distribute_and_run(self, urls: List[str], context: dict = None):
        for i, url in enumerate(urls):
            agent = self.agents[i % len(self.agents)]
            agent.crawl(url, context)
