
# crawler/expert.py
from typing import Dict, Any, Callable, List

class ExpertSystemInterface:
    def __init__(self):
        self.rules: List[Callable[[Dict[str, Any]], bool]] = []
        self.context = {}

    def add_rule(self, rule_func: Callable[[Dict[str, Any]], bool]):
        self.rules.append(rule_func)

    def set_context(self, context: Dict[str, Any]):
        self.context = context

    def process_knowledge(self, knowledge: Dict[str, Any]) -> bool:
        for rule in self.rules:
            passed = rule(knowledge)
            if not passed:
                print(f"[RULE FAILED] {knowledge.get('title', 'n/a')}")
                return False
        print(f"[RULE PASSED] {knowledge.get('title', 'n/a')}")
        return True

    def clear_rules(self):
        self.rules = []