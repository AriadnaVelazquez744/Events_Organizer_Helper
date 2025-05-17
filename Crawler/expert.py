
# crawler/expert.py
from typing import Dict, Any, Callable, List

class ExpertSystemInterface:
    def __init__(self):
        self.rules: List[Callable[[Dict[str, Any]], None]] = []

    def add_rule(self, rule_func: Callable[[Dict[str, Any]], None]):
        self.rules.append(rule_func)

    def process_knowledge(self, knowledge: Dict[str, Any]):
        for rule in self.rules:
            rule(knowledge)
