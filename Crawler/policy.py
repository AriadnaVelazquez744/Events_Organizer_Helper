
# crawler/policy.py
import time
from urllib.robotparser import RobotFileParser
from urllib.parse import urlparse
import requests

class CrawlPolicy:
    def __init__(self, user_agent="MyCrawlerBot", delay=1.0):
        self.user_agent = user_agent
        self.delay = delay
        self.robots_cache = {}

    def can_fetch(self, url: str) -> bool:
        domain = urlparse(url).scheme + "://" + urlparse(url).netloc
        if domain not in self.robots_cache:
            robots_url = domain + "/robots.txt"
            rp = RobotFileParser()
            try:
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except Exception:
                self.robots_cache[domain] = None
                return True  # Si falla, asumimos permitido
        rp = self.robots_cache.get(domain)
        return rp.can_fetch(self.user_agent, url) if rp else True

    def wait(self):
        time.sleep(self.delay)
