
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
        for idx, rule in enumerate(self.rules):
            try:
                passed = rule(knowledge)
            except Exception as e:
                print(f"[RULE ERROR] Excepción en regla {idx}: {e}")
                return False

            if not passed:
                title = knowledge.get("title") or knowledge.get("nombre") or "n/a"
                print(f"[RULE FAILED] {title} en regla {idx}")
                return False
        title = knowledge.get("title") or knowledge.get("nombre") or "n/a"
        print(f"[RULE PASSED] {title}")
        return True


    def clear_rules(self):
        self.rules = []