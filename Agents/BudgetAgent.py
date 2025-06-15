# agents/budget_distributor.py

import os
import json
import random
import math
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from planner_rag import PlannerRAG

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

@dataclass
class ServiceConstraints:
    min_budget: float
    max_budget: float
    quality_threshold: float
    required_features: List[str]

class BudgetDistributorAgent:
    def __init__(self, memory_file="user_pref_memory.json"):
        self.categories = ["venue", "catering", "decor"]
        self.memory_file = memory_file
        self.history = self._load_memory()
        self.service_constraints = self._initialize_constraints()
        self.rag = PlannerRAG()  # Inicializa el sistema RAG
        
    def _load_knowledge_graph(self, category: str) -> Dict:
        """Carga el grafo de conocimiento correspondiente a la categoría."""
        graph_file = f"{category}_graph.json"
        if os.path.exists(graph_file):
            with open(graph_file, 'r') as f:
                return json.load(f)
        return {}

    def _extract_price_range(self, data: Dict) -> Tuple[float, float]:
        """Extrae el rango de precios de los datos del grafo."""
        prices = []
        
        for item in data.values():
            if isinstance(item, dict):
                # Maneja diferentes formatos de precio
                if 'price' in item:
                    price = item['price']
                    if isinstance(price, (int, float)):
                        prices.append(price)
                    elif isinstance(price, str):
                        # Intenta extraer números de strings
                        try:
                            num = float(''.join(filter(str.isdigit, price)))
                            prices.append(num)
                        except ValueError:
                            continue
                    elif isinstance(price, dict):
                        # Maneja estructuras de precio complejas
                        for value in price.values():
                            if isinstance(value, (int, float)):
                                prices.append(value)
                            elif isinstance(value, str):
                                try:
                                    num = float(''.join(filter(str.isdigit, value)))
                                    prices.append(num)
                                except ValueError:
                                    continue
                elif 'minimum_spend' in item:
                    prices.append(item['minimum_spend'])
                elif 'starting_price' in item:
                    prices.append(item['starting_price'])

        if not prices:
            return 0.0, float('inf')
            
        return min(prices), max(prices)

    def _extract_required_features(self, data: Dict) -> List[str]:
        """Extrae las características requeridas basadas en los datos disponibles."""
        features = set()
        
        for item in data.values():
            if isinstance(item, dict):
                # Añade campos que son comunes y relevantes
                for key in item.keys():
                    if key not in ['price', 'name', 'description', 'id']:
                        features.add(key)
                        
        return list(features)

    def _initialize_constraints(self) -> Dict[str, ServiceConstraints]:
        """Inicializa las restricciones basadas en los datos reales de los grafos."""
        constraints = {}
        
        for category in self.categories:
            data = self._load_knowledge_graph(category)
            if not data:
                print(f"[⚠️] No se encontró el grafo de conocimiento para {category}")
                continue
                
            min_price, max_price = self._extract_price_range(data)
            required_features = self._extract_required_features(data)
            
            # Ajusta los umbrales basados en los datos reales
            quality_threshold = 0.6  # Valor base que puede ajustarse según la calidad de los datos
            
            constraints[category] = ServiceConstraints(
                min_budget=min_price,
                max_budget=max_price,
                quality_threshold=quality_threshold,
                required_features=required_features
            )
            
            print(f"[📊] Restricciones para {category}:")
            print(f"  - Rango de precios: ${min_price:,.2f} - ${max_price:,.2f}")
            print(f"  - Características requeridas: {', '.join(required_features)}")
            
        return constraints
        
    def _load_memory(self) -> Dict[str, Dict[str, float]]:
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return {}

    def _save_memory(self):
        with open(self.memory_file, "w") as f:
            json.dump(self.history, f, indent=2)

    def infer_priorities(self, user_text: str) -> Dict[str, float]:
        """Infiere prioridades usando LLM con un prompt más estructurado."""
        prompt = f"""
Given this user's wedding description: 
"{user_text}"

Analyze the text and assign importance weights to these categories:
{", ".join(self.categories)}

Consider:
1. Explicit mentions of preferences
2. Implicit priorities based on description
3. Cultural and social context
4. Practical requirements

Your response must be a JSON with this exact structure:
{{ "venue": 0.3, "catering": 0.2, ... }}

The weights should:
- Sum to 1.0
- Reflect relative importance
- Consider both stated and implied preferences
"""
        try:
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-8b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            weights = json.loads(content)
            return self._normalize_weights(weights)
        except Exception as e:
            print("[LLM ERROR]", e)
            return self._get_default_weights()

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normaliza los pesos para que sumen 1.0."""
        total = sum(weights.values())
        if total == 0:
            return self._get_default_weights()
        return {k: v/total for k, v in weights.items()}

    def _get_default_weights(self) -> Dict[str, float]:
        """Retorna pesos por defecto basados en prioridades típicas."""
        return {
            "venue": 0.4,  # Típicamente la mayor inversión
            "catering": 0.35,  # Segunda prioridad
            "decor": 0.25  # Menor prioridad
        }
        
    def merge_with_history(self, user_id: str, new_weights: Dict[str, float]) -> Dict[str, float]:
        """Fusiona nuevas preferencias con el historial usando un sistema de aprendizaje adaptativo."""
        prev = self.history.get(user_id)
        if not prev:
            self.history[user_id] = new_weights
            self._save_memory()
            return new_weights

        # Ajusta el factor de aprendizaje basado en la consistencia
        consistency = self._calculate_consistency(prev, new_weights)
        learning_rate = 0.7 + (0.3 * consistency)  # Más peso a nuevas preferencias si son consistentes

        merged = {
            k: learning_rate * new_weights.get(k, 0) + 
               (1 - learning_rate) * prev.get(k, 0) 
            for k in self.categories
        }
        
        self.history[user_id] = self._normalize_weights(merged)
        self._save_memory()
        return self.history[user_id]

    def _calculate_consistency(self, prev: Dict[str, float], new: Dict[str, float]) -> float:
        """Calcula la consistencia entre preferencias previas y nuevas."""
        if not prev or not new:
            return 0.0
        
        # Calcula la correlación de orden entre las preferencias
        prev_order = sorted(prev.items(), key=lambda x: -x[1])
        new_order = sorted(new.items(), key=lambda x: -x[1])
        
        # Calcula la distancia de Kendall Tau
        n = len(prev_order)
        if n < 2:
            return 1.0
            
        concordant = 0
        total = 0
        
        for i in range(n):
            for j in range(i+1, n):
                prev_i_rank = prev_order[i][0]
                prev_j_rank = prev_order[j][0]
                new_i_rank = new_order[i][0]
                new_j_rank = new_order[j][0]
                
                if (prev_i_rank == new_i_rank and prev_j_rank == new_j_rank) or \
                   (prev_i_rank == new_j_rank and prev_j_rank == new_i_rank):
                    concordant += 1
                total += 1
                
        return concordant / total if total > 0 else 0.0

    def optimize(self, weights: Dict[str, float], budget: int, iterations=1000) -> Dict[str, int]:
        """Optimiza la distribución del presupuesto usando Simulated Annealing mejorado."""
        def cost(state: Dict[str, int]) -> float:
            """Función de costo que considera múltiples factores."""
            # Costo base basado en preferencias
            base_cost = -sum(weights[k] * math.log(1 + state[k]) for k in state)
            
            # Penalización por violar restricciones
            constraint_penalty = 0
            for category, amount in state.items():
                if category in self.service_constraints:
                    constraints = self.service_constraints[category]
                    if amount < constraints.min_budget:
                        constraint_penalty += (constraints.min_budget - amount) * 2
                    if amount > constraints.max_budget:
                        constraint_penalty += (amount - constraints.max_budget) * 2
            
            # Penalización por desbalance
            balance_penalty = 0
            total = sum(state.values())
            if total != budget:
                balance_penalty = abs(total - budget) * 10
            
            return base_cost + constraint_penalty + balance_penalty

        def neighbor(state: Dict[str, int]) -> Dict[str, int]:
            """Genera un vecino válido respetando restricciones."""
            new_state = state.copy()
            k1, k2 = random.sample(list(state.keys()), 2)
            
            # Calcula el rango de cambio posible
            max_increase = min(
                self.service_constraints[k1].max_budget - state[k1],
                state[k2] - self.service_constraints[k2].min_budget
            )
            
            if max_increase > 0:
                delta = random.randint(1, min(100, max_increase))
                new_state[k1] += delta
                new_state[k2] -= delta
            
            return new_state

        # Inicialización mejorada
        current = self._initialize_state(weights, budget)
        best = current.copy()
        best_cost = cost(best)
        
        # Parámetros de Simulated Annealing
        initial_temp = 1000
        final_temp = 1
        alpha = 0.95
        
        current_temp = initial_temp
        while current_temp > final_temp:
            for _ in range(iterations):
                candidate = neighbor(current)
                candidate_cost = cost(candidate)
                delta = candidate_cost - cost(current)
                
                if delta < 0 or random.random() < math.exp(-delta / current_temp):
                    current = candidate
                    if candidate_cost < best_cost:
                        best = candidate
                        best_cost = candidate_cost
            
            current_temp *= alpha
        
        return self._normalize_state(best, budget)

    def _initialize_state(self, weights: Dict[str, float], budget: int) -> Dict[str, int]:
        """Inicializa un estado válido respetando restricciones."""
        # Primero obtiene la recomendación del RAG
        rag_distribution = self.rag.get_budget_distribution(budget)
        
        # Convierte la distribución del RAG a un estado inicial
        state = {k: int(v) for k, v in rag_distribution.items() if k in self.categories}
        
        # Ajusta según las restricciones
        for category in self.categories:
            if category in state:
                constraints = self.service_constraints[category]
                state[category] = max(min(state[category], constraints.max_budget), constraints.min_budget)
        
        return state

    def _normalize_state(self, state: Dict[str, int], budget: int) -> Dict[str, int]:
        """Normaliza el estado final para que sume exactamente el presupuesto."""
        current_sum = sum(state.values())
        if current_sum == 0:
            return {k: 0 for k in state}
            
        # Ajusta proporcionalmente
        factor = budget / current_sum
        scaled = {k: int(v * factor) for k, v in state.items()}
        
        # Ajusta el residuo
        diff = budget - sum(scaled.values())
        if diff != 0:
            # Asigna el residuo a la categoría con mayor peso
            max_category = max(self.history.get("current", self._get_default_weights()).items(), 
                             key=lambda x: x[1])[0]
            scaled[max_category] += diff
        
        return scaled
    
    def explain_allocation(self, user_id: str, allocation: Dict[str, int]) -> str:
        """Genera una explicación detallada de la asignación."""
        pref = self.history.get(user_id, {})
        if not pref:
            return "No tengo historial suficiente para este usuario aún."
            
        # Ordena las categorías por prioridad
        sorted_pref = sorted(pref.items(), key=lambda x: -x[1])
        
        # Genera explicación detallada
        explanation = "Basado en tus preferencias y los datos disponibles:\n"
        for category, weight in sorted_pref:
            amount = allocation[category]
            percentage = (amount / sum(allocation.values())) * 100
            explanation += f"\n- {category.title()}: ${amount:,} ({percentage:.1f}% del presupuesto)"
            
            # Añade información sobre el rango de precios disponible
            if category in self.service_constraints:
                constraints = self.service_constraints[category]
                explanation += f"\n  Rango disponible: ${constraints.min_budget:,.2f} - ${constraints.max_budget:,.2f}"
            
            if weight > 0.4:
                explanation += " (Alta prioridad)"
            elif weight < 0.2:
                explanation += " (Baja prioridad)"
                
        return explanation

    def run(self, user_id: str, total_budget: int, user_description: str) -> Dict[str, int]:
        """Ejecuta el proceso completo de distribución de presupuesto."""
        print("[🧠] Infiriendo prioridades iniciales...")
        inferred = self.infer_priorities(user_description)
        print("[📊] Pesos inferidos por LLM:", inferred)

        merged = self.merge_with_history(user_id, inferred)
        print("[🔁] Preferencias fusionadas con historial:", merged)

        print("[📈] Optimizando distribución final...")
        final = self.optimize(merged, total_budget)
        
        # Actualiza patrones de éxito en RAG
        self.rag.update_success_pattern(
            "budget_management",
            {
                "total_budget": total_budget,
                "distribution": final,
                "success_rate": 0.95  # Asumimos éxito si llegamos aquí
            }
        )
        
        print("[✅] Resultado final:")
        for k, v in final.items():
            print(f"- {k}: ${v:,}")
            
        print("\n[📝] Explicación:")
        print(self.explain_allocation(user_id, final))
        
        return final