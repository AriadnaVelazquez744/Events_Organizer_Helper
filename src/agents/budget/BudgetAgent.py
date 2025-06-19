# agents/budget_distributor.py

import os
import json
import random
import math
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI
from src.agents.planner.planner_rag import PlannerRAG

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
        # Mapeo de categorías a nombres de archivo
        file_mapping = {
            "venue": "venues_graph.json",  # Nombre correcto para venues
            "catering": "catering_graph.json",
            "decor": "decor_graph.json"
        }
        
        # Obtener el directorio actual del script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        inter = os.path.join(parent_dir, category)
        graph_file = os.path.join(inter, file_mapping.get(category, f"{category}_graph.json"))
        
        print(f"[BudgetDistributorAgent] Intentando cargar grafo para {category}")
        print(f"[BudgetDistributorAgent] Ruta del archivo: {graph_file}")
        print(f"[BudgetDistributorAgent] ¿Existe el archivo?: {os.path.exists(graph_file)}")
        
        try:
            if os.path.exists(graph_file):
                with open(graph_file, 'r') as f:
                    data = json.load(f)
                    print(f"[BudgetDistributorAgent] Grafo cargado exitosamente para {category}")
                    return data
            print(f"[⚠️] No se encontró el archivo de conocimiento para {category}: {graph_file}")
            return {}
        except json.JSONDecodeError as e:
            print(f"[⚠️] Error al decodificar {graph_file}: {str(e)}")
            return {}
        except Exception as e:
            print(f"[⚠️] Error inesperado al cargar {graph_file}: {str(e)}")
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
            
            # print(f"[📊] Restricciones para {category}:")
            # print(f"  - Rango de precios: ${min_price:,.2f} - ${max_price:,.2f}")
            # print(f"  - Características requeridas: {', '.join(required_features)}")
            
        return constraints
        
    def _load_memory(self) -> dict:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        memory_path = os.path.join(current_dir, self.memory_file)
        if os.path.exists(memory_path):
            with open(memory_path, "r") as f:
                print(f"[BudgetDistributorAgent] Cargando historial de preferencias desde: {memory_path}")
                try:
                    data = json.load(f)
                    # Asegura la estructura
                    if not isinstance(data, dict):
                        data = {"usuarios": {}, "sesiones": {}}
                    if "usuarios" not in data:
                        data["usuarios"] = {}
                    if "sesiones" not in data:
                        data["sesiones"] = {}
                    return data
                except Exception as e:
                    print(f"[BudgetDistributorAgent] Error cargando historial: {e}")
                    return {"usuarios": {}, "sesiones": {}}
        print(f"[BudgetDistributorAgent] No se encontró historial de preferencias en: {memory_path}")
        return {"usuarios": {}, "sesiones": {}}

    def _save_memory(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        memory_path = os.path.join(current_dir, self.memory_file)
        with open(memory_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def get_user_id(self, session_id: str) -> str:
        # Si no existe, retorna el session_id como fallback
        return self.history.get("sesiones", {}).get(session_id, session_id)

    def save_preferences(self, user_id: str, session_id: str, prefs: dict):
        self.history.setdefault("usuarios", {})[user_id] = prefs
        self.history.setdefault("sesiones", {})[session_id] = user_id
        self._save_memory()

    def get_preferences(self, user_id: str) -> dict:
        return self.history.get("usuarios", {}).get(user_id, {})

    def infer_priorities(self, user_text: str) -> Dict[str, float]:
        """Infiere prioridades usando LLM con un prompt más estructurado."""
        print("[BudgetDistributorAgent] Intentando inferir prioridades del texto del usuario...")
        
        try:
            # Parsear los criterios del JSON
            criteria = json.loads(user_text)
            
            prompt = f"""
Based on these wedding planning criteria:

Venue Requirements:
- Capacity: {criteria.get('venue', {}).get('capacity', 0)} guests
- Location: {criteria.get('venue', {}).get('location', 'Not specified')}
- Required Features: {', '.join(criteria.get('venue', {}).get('obligatorios', []))}

Catering Requirements:
- Meal Types: {', '.join(criteria.get('catering', {}).get('meal_types', []))}
- Dietary Options: {', '.join(criteria.get('catering', {}).get('dietary_options', []))}
- Required Features: {', '.join(criteria.get('catering', {}).get('obligatorios', []))}

Decor Requirements:
- Service Level: {', '.join(criteria.get('decor', {}).get('service_levels', []))}
- Floral Arrangements: {', '.join(criteria.get('decor', {}).get('floral_arrangements', []))}
- Required Features: {', '.join(criteria.get('decor', {}).get('obligatorios', []))}

Total Budget: ${criteria.get('presupuesto_total', 0)}
Guest Count: {criteria.get('guest_count', 0)}
Style: {criteria.get('style', 'Not specified')}

Assign importance weights to these categories:
{", ".join(self.categories)}

IMPORTANT: Your response must be ONLY a valid JSON object with this exact structure:
{{ "venue": value, "catering": value, "decor": value }}

The weights should:
- Sum to 1.0
- Reflect relative importance based on the specific requirements
- Consider the complexity and scope of each category's requirements
- Take into account the total budget and guest count

DO NOT include any additional text or explanation. ONLY return the JSON object.
"""
            print("[BudgetDistributorAgent] Enviando prompt a la API...")
            print(f"[BudgetDistributorAgent] Prompt: {prompt}")
            
            response = client.chat.completions.create(
                model="meta-llama/llama-3.3-8b-instruct:free",
                messages=[{"role": "user", "content": prompt}]
            )
            
            if not response or not response.choices:
                print("[BudgetDistributorAgent] No se recibió respuesta válida de la API")
                return self._get_default_weights()
                
            content = response.choices[0].message.content
            print(f"[BudgetDistributorAgent] Respuesta recibida: {content}")
            
            try:
                weights = json.loads(content)
                print(f"[BudgetDistributorAgent] Pesos parseados: {weights}")
                return self._normalize_weights(weights)
            except json.JSONDecodeError as e:
                print(f"[BudgetDistributorAgent] Error al parsear JSON: {str(e)}")
                return self._get_default_weights()
                
        except Exception as e:
            print(f"[BudgetDistributorAgent] Error al inferir prioridades: {str(e)}")
            print("[BudgetDistributorAgent] Usando distribución por defecto")
            return self._get_default_weights()

    def _normalize_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """Normaliza los pesos para que sumen 1.0."""
        print("[BudgetDistributorAgent] Normalizando pesos...")
        
        # Verifica que todos los pesos sean números válidos
        valid_weights = {}
        for category in self.categories:
            try:
                weight = float(weights.get(category, 0))
                if weight >= 0:
                    valid_weights[category] = weight
                else:
                    print(f"[BudgetDistributorAgent] Peso negativo encontrado para {category}: {weight}")
                    valid_weights[category] = 0
            except (ValueError, TypeError):
                print(f"[BudgetDistributorAgent] Peso inválido encontrado para {category}: {weights.get(category)}")
                valid_weights[category] = 0
        
        total = sum(valid_weights.values())
        if total == 0:
            print("[BudgetDistributorAgent] Suma de pesos es 0, usando distribución por defecto")
            return self._get_default_weights()
            
        normalized = {k: v/total for k, v in valid_weights.items()}
        print(f"[BudgetDistributorAgent] Pesos normalizados: {normalized}")
        return normalized

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

    def optimize(self, weights: Dict[str, float], budget: int, iterations=100) -> Dict[str, int]:
        """Optimiza la distribución del presupuesto usando Simulated Annealing mejorado."""
        print(f"[BudgetDistributorAgent] Iniciando optimización con Simulated Annealing")
        print(f"[BudgetDistributorAgent] Usando pesos fijos: {weights}")
        print(f"[BudgetDistributorAgent] Presupuesto total: {budget}")
        
        def cost(state: Dict[str, float]) -> float:
            """Función de costo que considera múltiples factores."""
            try:
                # Costo base basado en preferencias (usando los pesos fijos)
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
                    
                if abs(total - budget) > 0.01:  # Permitir un pequeño margen de error
                    balance_penalty = abs(total - budget) * 10
                    
                    final_cost = base_cost + constraint_penalty + balance_penalty
                    return final_cost
            except Exception as e:
                print(f"[BudgetDistributorAgent] Error en cálculo de costo: {str(e)}")
                return float('inf')

        def neighbor(state: Dict[str, float]) -> Dict[str, float]:
            """Genera un vecino válido respetando restricciones."""
            new_state = state.copy()
            k1, k2 = random.sample(list(state.keys()), 2)
            
            # Calcula el rango de cambio posible
            max_increase = min(
                self.service_constraints[k1].max_budget - state[k1],
                state[k2] - self.service_constraints[k2].min_budget
            )
            
            if max_increase > 0:
                # Reducir el tamaño del cambio para mejor convergencia
                delta = random.uniform(0.1, min(10, max_increase))
                new_state[k1] = state[k1] + delta
                new_state[k2] = state[k2] - delta
            
            return new_state

        def initialize_state() -> Dict[str, float]:
            """Inicializa un estado válido respetando restricciones."""
            # Primero obtiene la recomendación del RAG
            rag_distribution = self.rag.get_budget_distribution(budget)
            
            # Convierte la distribución del RAG a un estado inicial
            state = {k: float(v) for k, v in rag_distribution.items() if k in self.categories}
            
            # Ajusta según las restricciones
            for category in self.categories:
                if category in state:
                    constraints = self.service_constraints[category]
                    state[category] = max(min(state[category], constraints.max_budget), constraints.min_budget)
            
            return state

        def normalize_state(state: Dict[str, float]) -> Dict[str, int]:
            """Normaliza el estado final para que sume exactamente el presupuesto."""
            # Primero redondeamos todos los valores
            rounded = {k: round(v) for k, v in state.items()}
            
            # Calculamos la diferencia con el presupuesto total
            total = sum(rounded.values())
            diff = budget - total
            
            if diff != 0:
                # Ajustamos la categoría con mayor peso
                max_weight_category = max(weights.items(), key=lambda x: x[1])[0]
                rounded[max_weight_category] += diff
            
            return rounded

        # Inicialización mejorada
        current = initialize_state()
        print(f"[BudgetDistributorAgent] Estado inicial: {current}")
        best = current.copy()
        best_cost = cost(best)
        print(f"[BudgetDistributorAgent] Costo inicial: {best_cost}")
        
        # Parámetros de Simulated Annealing ajustados
        initial_temp = 100
        final_temp = 0.1
        alpha = 0.95
        max_iterations = 1000  # Límite total de iteraciones
        
        current_temp = initial_temp
        iteration = 0
        no_improvement_count = 0
        
        while current_temp > final_temp and iteration < max_iterations:
            improved = False
            for _ in range(iterations):
                candidate = neighbor(current)
                candidate_cost = cost(candidate)
                delta = candidate_cost - cost(current)
                
                if delta < 0 or random.random() < math.exp(-delta / current_temp):
                    current = candidate
                    if candidate_cost < best_cost:
                        best = candidate
                        best_cost = candidate_cost
                        improved = True
                        no_improvement_count = 0
                        print(f"[BudgetDistributorAgent] Nueva mejor solución encontrada en iteración {iteration}: {best} (costo: {best_cost})")
                
                iteration += 1
                if iteration >= max_iterations:
                    break
            
            if not improved:
                no_improvement_count += 1
                if no_improvement_count >= 5:  # Si no hay mejora en 5 ciclos, terminar
                    print("[BudgetDistributorAgent] No se encontraron mejoras en los últimos ciclos, terminando...")
                    break
            
            current_temp *= alpha
        
        final_state = normalize_state(best)
        print(f"[BudgetDistributorAgent] Estado final: {final_state}")
        print(f"[BudgetDistributorAgent] Costo final: {cost(final_state)}")
        return final_state
    
    def explain_allocation(self, user_id: str, allocation: Dict[str, int], new_weights: Dict[str, float] = None) -> str:
        """Genera una explicación detallada de la asignación incluyendo información del historial."""
        user_history = self.history.get(user_id, {})
        
        if not user_history:
            return "Esta es tu primera consulta. Las preferencias se han inferido de tus criterios actuales."
        
        # Calcular consistencia si se proporcionan nuevas preferencias
        consistency_info = ""
        if new_weights:
            consistency = self._calculate_consistency(user_history, new_weights)
            if consistency > 0.7:
                consistency_info = f"\n\n📊 **Consistencia Alta ({consistency:.1f})**: Tus preferencias son muy similares a consultas anteriores."
            elif consistency > 0.4:
                consistency_info = f"\n\n📊 **Consistencia Media ({consistency:.1f})**: Tus preferencias han cambiado moderadamente."
            else:
                consistency_info = f"\n\n📊 **Consistencia Baja ({consistency:.1f})**: Tus preferencias han cambiado significativamente."
        
        # Ordena las categorías por prioridad del historial
        sorted_history = sorted(user_history.items(), key=lambda x: -x[1])
        
        # Genera explicación detallada
        explanation = f"Basado en tu historial de preferencias y los criterios actuales:{consistency_info}\n"
        
        explanation += "\n**Distribución del Presupuesto:**"
        for category, weight in sorted_history:
            amount = allocation[category]
            percentage = (amount / sum(allocation.values())) * 100
            explanation += f"\n- **{category.title()}**: ${amount:,} ({percentage:.1f}% del presupuesto)"
            
            # Añade información sobre el rango de precios disponible
            if category in self.service_constraints:
                constraints = self.service_constraints[category]
                explanation += f"\n  💰 Rango disponible: ${constraints.min_budget:,.2f} - ${constraints.max_budget:,.2f}"
            
            # Añade información sobre la prioridad histórica
            if weight > 0.4:
                explanation += " 🔥 (Alta prioridad histórica)"
            elif weight < 0.2:
                explanation += " ⚡ (Baja prioridad histórica)"
            else:
                explanation += " ⚖️ (Prioridad media histórica)"
        
        # Añadir información sobre el aprendizaje
        explanation += f"\n\n💡 **Sistema de Aprendizaje**: "
        explanation += "El sistema ha aprendido de tus consultas anteriores para proporcionar "
        explanation += "distribuciones más precisas y consistentes con tus preferencias."
        
        return explanation

    def run(self, user_id: str, total_budget: int, user_description: str, session_id: str = None) -> Dict[str, int]:
        """Ejecuta el proceso completo de distribución de presupuesto."""
        print(f"[BudgetDistributorAgent] Iniciando distribución de presupuesto para {total_budget}...")
        # Si session_id está presente, obtener el user_id real
        # if session_id:
        #     user_id = self.get_user_id(session_id)
        print(f"[BudgetDistributorAgent] user_id usado: {user_id}")
        print(f"[BudgetDistributorAgent] Claves en historial de usuarios: {list(self.history.get('usuarios', {}).keys())}")
        # 1. Obtener preferencias del historial del usuario
        user_history = self.get_preferences(user_id)
        print(f"[BudgetDistributorAgent] Historial del usuario: {user_history}")
        # 2. Inferir nuevas preferencias del texto del usuario
        print("[BudgetDistributorAgent] Inferiendo nuevas prioridades...")
        new_weights = self.infer_priorities(user_description)
        print(f"[BudgetDistributorAgent] Nuevas preferencias inferidas: {new_weights}")
        # 3. Verificar que las nuevas preferencias sean válidas
        if not all(0 <= w <= 1 for w in new_weights.values()):
            print("[BudgetDistributorAgent] Nuevas preferencias inválidas, usando distribución por defecto")
            new_weights = self._get_default_weights()
        # 4. Fusionar con el historial del usuario
        if user_history:
            print("[BudgetDistributorAgent] Fusionando con historial del usuario...")
            consistency = self._calculate_consistency(user_history, new_weights)
            print(f"[BudgetDistributorAgent] Consistencia con historial: {consistency:.2f}")
            # Si hay alta consistencia, dar más peso al historial
            if consistency > 0.7:
                print("[BudgetDistributorAgent] Alta consistencia detectada, priorizando historial")
                final_weights = self.merge_with_history(user_id, new_weights)
            else:
                print("[BudgetDistributorAgent] Baja consistencia, dando más peso a nuevas preferencias")
                learning_rate = 0.8  # 80% peso a nuevas preferencias
                merged = {
                    k: learning_rate * new_weights.get(k, 0) + 
                       (1 - learning_rate) * user_history.get(k, 0) 
                    for k in self.categories
                }
                final_weights = self._normalize_weights(merged)
                self.save_preferences(user_id, session_id or user_id, final_weights)
        else:
            print("[BudgetDistributorAgent] Sin historial previo, usando nuevas preferencias")
            final_weights = new_weights
            self.save_preferences(user_id, session_id or user_id, final_weights)
        print(f"[BudgetDistributorAgent] Pesos finales después de fusión: {final_weights}")
        # 5. Optimizar distribución usando los pesos fusionados
        print("[BudgetDistributorAgent] Iniciando optimización con pesos fusionados...")
        try:
            distribution = self.optimize(final_weights, total_budget)
            print(f"[BudgetDistributorAgent] Distribución final: {distribution}")
            if not distribution or sum(distribution.values()) != total_budget:
                print("[BudgetDistributorAgent] Distribución inválida, usando distribución proporcional")
                distribution = {
                    category: int(total_budget * weight)
                    for category, weight in final_weights.items()
                }
                diff = total_budget - sum(distribution.values())
                if diff != 0:
                    max_category = max(final_weights.items(), key=lambda x: x[1])[0]
                    distribution[max_category] += diff
        except Exception as e:
            print(f"[BudgetDistributorAgent] Error en optimización: {str(e)}")
            print("[BudgetDistributorAgent] Usando distribución proporcional simple")
            distribution = {
                category: int(total_budget * weight)
                for category, weight in final_weights.items()
            }
            diff = total_budget - sum(distribution.values())
            if diff != 0:
                max_category = max(final_weights.items(), key=lambda x: x[1])[0]
                distribution[max_category] += diff
        print(f"[BudgetDistributorAgent] Distribución final validada: {distribution}")
        print(f"[BudgetDistributorAgent] Suma total: {sum(distribution.values())}")
        return distribution

    def receive(self, message: Dict[str, Any]):
        """Procesa mensajes entrantes."""
        if message["tipo"] == "task":
            print(message)
            task_id = message["contenido"]["task_id"]
            parameters = message["contenido"]["parameters"]
            session_id = message["session_id"]
            user_id = message["user_id"]
            print(f"user_id extraído {user_id}")  # <--- Extraer user_id real
            try:
                print(f"[BudgetDistributorAgent] Procesando tarea de distribución de presupuesto")
                total_budget = parameters.get("budget", 0)
                criteria = parameters.get("criterios", {})
                print(f"[BudgetDistributorAgent] Criterios recibidos: {json.dumps(criteria, indent=2)}")
                # Ejecutar la distribución del presupuesto
                distribution = self.run(
                    user_id=user_id,
                    total_budget=total_budget,
                    user_description=json.dumps(criteria),
                    session_id=session_id
                )
                # Obtener las nuevas preferencias para la explicación
                new_weights = self.infer_priorities(json.dumps(criteria))
                explanation = self.explain_allocation(user_id, distribution, new_weights)
                return {
                    "origen": "BudgetDistributorAgent",
                    "destino": message["origen"],
                    "tipo": "agent_response",
                    "contenido": {
                        "task_id": task_id,
                        "distribution": distribution,
                        "explanation": explanation,
                        "user_preferences": self.get_preferences(user_id)
                    },
                    "session_id": session_id
                }
            except Exception as e:
                print(f"[BudgetDistributorAgent] Error procesando tarea: {str(e)}")
                return {
                    "origen": "BudgetDistributorAgent",
                    "destino": message["origen"],
                    "tipo": "error",
                    "contenido": {
                        "task_id": task_id,
                        "error": str(e)
                    },
                    "session_id": session_id
                }
        else:
            print(f"[BudgetDistributorAgent] Tipo de mensaje no reconocido: {message['tipo']}")