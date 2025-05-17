
# crawler/manager.py
from typing import List
from core import CrawlerAgent

class CrawlerManager:
    def __init__(self, agents: List[CrawlerAgent]):
        self.agents = agents

    def distribute_and_run(self, urls: List[str]):
        for i, url in enumerate(urls):
            agent = self.agents[i % len(self.agents)]
            agent.crawl(url)
