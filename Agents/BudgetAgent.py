
# agents/budget_distributor.py

import os
import json
import random
import math
import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, List

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

class BudgetDistributorAgent:
    def __init__(self, memory_file="user_pref_memory.json"):
        self.categories = ["venue", "catering", "decor"]
        self.memory_file = memory_file
        self.history = self._load_memory()
        
    def _load_memory(self) -> Dict[str, Dict[str, float]]:
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {}

    def _save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def infer_priorities(self, user_text: str) -> Dict[str, float]:
        prompt = f"""
Given this user text: 
"{user_text}"

Assign a relative importance to each of these categories:
{", ".join(self.categories)}

Distribute a total sum of 1 among them. Your response must be exactly a JSON with this exact structure, without any notes or reviews after, make shure that the json has a correct structure:
{{ "venue": 0.3, "catering": 0.2, ... }}
"""
        try:
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-8b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            weights = json.loads(content)
            return weights
        except Exception as e:
            print("[LLM ERROR]", e)
            n = len(self.categories)
            return {k: 1/n for k in self.categories}
        
    def merge_with_history(self, user_id: str, new_weights: Dict[str, float]) -> Dict[str, float]:
        prev = self.history.get(user_id)
        if not prev:
            self.history[user_id] = new_weights
            self._save_memory()
            return new_weights
        merged = {k: 0.7 * new_weights.get(k, 0) + 0.3 * prev.get(k, 0) for k in self.categories}
        self.history[user_id] = merged
        self._save_memory()
        return merged

    def optimize(self, weights: Dict[str, float], budget: int, iterations=1000, temp=1000) -> Dict[str, int]:
        state = {k: int(budget * weights[k]) for k in weights}

        def cost(s):
            return -sum(weights[k] * math.log(1 + s[k]) for k in s)

        def neighbor(s):
            s_new = s.copy()
            k1, k2 = random.sample(list(s.keys()), 2)
            delta = random.randint(-100, 100)
            s_new[k1] = max(0, s_new[k1] + delta)
            s_new[k2] = max(0, s_new[k2] - delta)
            return self._normalize(s_new, budget)

        best = current = state.copy()

        for i in range(iterations):
            T = temp / (1 + i)
            candidate = neighbor(current)
            Δ = cost(candidate) - cost(current)
            if Δ < 0 or random.random() < math.exp(-Δ / T):
                current = candidate
                if cost(current) < cost(best):
                    best = current

        return best

    def _normalize(self, s: Dict[str, int], total: int) -> Dict[str, int]:
        current_sum = sum(s.values())
        if current_sum == 0:
            return {k: 0 for k in s}
        factor = total / current_sum
        scaled = {k: int(v * factor) for k, v in s.items()}
        diff = total - sum(scaled.values())
        if diff != 0:
            k = random.choice(list(scaled))
            scaled[k] += diff
        return scaled
    
    def explain_allocation(self, user_id: str) -> str:
        pref = self.history.get(user_id, {})
        if not pref:
            return "No tengo historial suficiente para este usuario aún."
        sorted_pref = sorted(pref.items(), key=lambda x: -x[1])
        top = sorted_pref[0]
        return f"Basado en tu historial, priorizas más '{top[0]}' con un peso de {top[1]:.2f}."

    def run(self, user_id: str, total_budget: int, user_description: str) -> Dict[str, int]:
        print("[🧠] Infiriendo prioridades iniciales...")
        inferred = self.infer_priorities(user_description)
        print("[📊] Pesos inferidos por LLM:", inferred)

        merged = self.merge_with_history(user_id, inferred)
        print("[🔁] Preferencias fusionadas con historial:", merged)

        print("[📈] Optimizando distribución final...")
        final = self.optimize(merged, total_budget)
        print("[✅] Resultado final:")
        for k, v in final.items():
            print(f"- {k}: ${v}")
        return final