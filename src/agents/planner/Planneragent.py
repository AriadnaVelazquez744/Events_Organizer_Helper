# agents/planner_agent_bdi.py
import queue
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from agents.beliefs_schema import BeliefState
from agents.session_memory import SessionMemoryManager
from agents.planner.planner_rag import PlannerRAG

@dataclass
class Task:
    id: str
    type: str
    parameters: Dict[str, Any]
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None
    retry_count: int = 0  # Contador de reintentos

@dataclass
class Desire:
    """Representa un deseo/objetivo del agente."""
    id: str
    type: str
    priority: float
    parameters: Dict[str, Any]
    status: str = "active"
    created_at: str = ""

@dataclass
class Intention:
    """Representa una intención/plan del agente."""
    id: str
    desire_id: str
    tasks: List[str]  # Lista de task IDs
    status: str = "active"
    created_at: str = ""

class PlannerAgentBDI:
    def __init__(self, name: str, bus, memory_manager: SessionMemoryManager):
        self.name = name
        self.bus = bus
        self.memory_manager = memory_manager
        self.active_sessions: Dict[str, Dict] = {}  # session_id -> session_data
        self.task_queue: Dict[str, List[Task]] = {}  # session_id -> [tasks]
        self.current_task: Dict[str, Task] = {}  # session_id -> current_task
        self.desires: Dict[str, List[Desire]] = {}  # session_id -> [desires]
        self.intentions: Dict[str, List[Intention]] = {}  # session_id -> [intentions]
        self.rag = PlannerRAG()  # Inicializa el sistema RAG
        
    def create_session(self, user_id: str) -> str:
        """Crea una nueva sesión para un usuario."""
        session_id = str(uuid.uuid4())
        
        # Crear sesión en el SessionMemoryManager primero
        self.memory_manager.create_session(user_id, session_id)
        
        # Crear sesión en el agente
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "beliefs": BeliefState(),
            "is_correction": False,
            "original_session": None,
            "created_at": datetime.now().isoformat()
        }
        self.task_queue[session_id] = []
        self.desires[session_id] = []
        self.intentions[session_id] = []
        
        return session_id

    def handle_correction(self, original_session_id: str, user_id: str) -> str:
        """Maneja una corrección creando una nueva sesión vinculada a la original."""
        new_session_id = self.create_session(user_id)
        self.active_sessions[new_session_id]["is_correction"] = True
        self.active_sessions[new_session_id]["original_session"] = original_session_id
        
        # Copia los beliefs relevantes de la sesión original
        original_beliefs = self.active_sessions[original_session_id]["beliefs"]
        new_beliefs = self.active_sessions[new_session_id]["beliefs"]
        
        # Copia solo los elementos que no están en conflicto
        for key in ["criterios", "venue", "catering", "pastel"]:
            if not original_beliefs.has_conflicto(key):
                new_beliefs.set(key, original_beliefs.get(key))
        
        return new_session_id

    def receive(self, message: Dict[str, Any]):
        """Procesa mensajes entrantes y actualiza el estado."""
        session_id = message.get("session_id")
        if not session_id or session_id not in self.active_sessions:
            print(f"[⚠️] Sesión no válida: {session_id}")
            return {
                "origen": self.name,
                "destino": message["origen"],
                "tipo": "error",
                "contenido": f"Sesión no válida: {session_id}",
                "session_id": session_id
            }

        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        if message["tipo"] == "user_request":
            self._handle_user_request(session_id, message["contenido"])
            return {
                "origen": self.name,
                "destino": message["origen"],
                "tipo": "acknowledgment",
                "contenido": {
                    "message": "Petición recibida y en proceso",
                    "session_id": session_id
                },
                "session_id": session_id
            }
        elif message["tipo"] == "agent_response":
            print(f"[PlannerAgent] Procesando respuesta de agente para la sesión {session_id}")
            self._handle_agent_response(session_id, message)
            
            # Verificar si todas las tareas están completadas
            final_response = self._check_completion(session_id)
            if final_response:
                print(f"[PlannerAgent] Todas las tareas completadas, retornando respuesta final")
                return final_response
            
            print(f"[PlannerAgent] Tareas pendientes, enviando acknowledgment")
            return {
                "origen": self.name,
                "destino": message["origen"],
                "tipo": "acknowledgment",
                "contenido": {
                    "message": "Respuesta de agente procesada",
                    "session_id": session_id
                },
                "session_id": session_id
            }
        elif message["tipo"] == "correction_request":
            self._handle_correction_request(session_id, message["contenido"])
            return {
                "origen": self.name,
                "destino": message["origen"],
                "tipo": "acknowledgment",
                "contenido": {
                    "message": "Corrección recibida y en proceso",
                    "session_id": session_id
                },
                "session_id": session_id
            }
        else:
            return {
                "origen": self.name,
                "destino": message["origen"],
                "tipo": "error",
                "contenido": f"Tipo de mensaje no reconocido: {message['tipo']}",
                "session_id": session_id
            }

    def _handle_user_request(self, session_id: str, request: Dict[str, Any]):
        """Procesa una nueva petición del usuario usando el ciclo BDI completo."""
        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        print(f"[PlannerAgent] 🔄 Iniciando ciclo BDI para sesión {session_id}")
        
        # 1. BELIEFS: Actualizar beliefs con la nueva información
        if "criterios" in request:
            beliefs.set("criterios", request["criterios"])
            
            # Usa RAG para obtener recomendaciones de presupuesto
            if "presupuesto_total" in request["criterios"]:
                budget_distribution = self.rag.get_budget_distribution(
                    request["criterios"]["presupuesto_total"]
                )
                beliefs.set("presupuesto_asignado", budget_distribution)
                
                # Actualizar beliefs en el SessionMemoryManager
                self.memory_manager.update_beliefs(session_id, {
                    "criterios": request["criterios"],
                    "presupuesto_asignado": budget_distribution
                })

        # 2. DESIRES: Crear desires basados en la petición
        print("[PlannerAgent] 🎯 Creando desires...")
        desires = self._create_desires_from_request(session_id, request)
        self.desires[session_id] = desires
        print(f"[PlannerAgent] Creados {len(desires)} desires")

        # 3. INTENTIONS: Crear intentions basados en los desires
        print("[PlannerAgent] 📋 Creando intentions...")
        intentions = self._create_intentions_from_desires(session_id, desires)
        self.intentions[session_id] = intentions
        print(f"[PlannerAgent] Creadas {len(intentions)} intentions")

        # 4. Actualizar beliefs sobre el estado del sistema
        self._update_beliefs_from_environment(session_id)

        # 5. Iniciar el procesamiento de tareas
        print("[PlannerAgent] 🚀 Iniciando procesamiento de tareas...")
        self._process_next_task(session_id)

    def _handle_correction_request(self, session_id: str, correction: Dict[str, Any]):
        """Procesa una corrección del usuario."""
        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        # Identifica qué elementos necesitan ser recalculados
        affected_elements = self._identify_affected_elements(correction)
        
        # Usa RAG para obtener estrategias de resolución
        if "conflicto" in correction:
            strategies = self.rag.suggest_conflict_resolution(
                correction["conflicto"],
                correction
            )
            if strategies:
                beliefs.set("estrategias_resolucion", strategies)
        
        # Crea nuevas tareas solo para los elementos afectados
        self._create_correction_tasks(session_id, affected_elements, correction)
        
        # Inicia el procesamiento de tareas
        self._process_next_task(session_id)

    def _handle_agent_response(self, session_id: str, message: Dict[str, Any]):
        """Procesa la respuesta de un agente."""
        current_task = self.current_task.get(session_id)
        if not current_task:
            print(f"[⚠️] No hay tarea activa para la sesión {session_id}")
            return

        if message["tipo"] == "error":
            print(f"[PlannerAgent] Error en tarea {current_task.type}: {message['contenido']}")
            
            # Manejo inteligente de errores con estrategias de corrección
            self._handle_task_error(session_id, current_task, message["contenido"])
        else:
            current_task.status = "completed"
            current_task.result = message["contenido"]
            print(f"[PlannerAgent] Tarea {current_task.type} completada con éxito")
            
            # Mapeo de tipos de tarea a claves de belief
            task_to_belief = {
                "budget_distribution": "presupuesto_asignado",
                "venue_search": "venue",
                "catering_search": "catering",
                "decor_search": "decor"
            }
            
            belief_key = task_to_belief.get(current_task.type)
            if belief_key:
                # Preparar actualización de beliefs
                updates = {}
                
                # Actualizar el belief principal
                if "results" in message["contenido"]:
                    updates[belief_key] = message["contenido"]["results"]
                else:
                    updates[belief_key] = message["contenido"]
                
                # Actualizar el estado de completado
                updates["completado"] = {belief_key: True}
                
                # Actualizar beliefs en el SessionMemoryManager
                self.memory_manager.update_beliefs(session_id, updates)
                print(f"[PlannerAgent] Actualizado belief {belief_key} y su estado de completado")
                
                # Si se completó la distribución del presupuesto, crear tareas de búsqueda
                if current_task.type == "budget_distribution":
                    print("[PlannerAgent] Distribución de presupuesto completada, creando tareas de búsqueda...")
                    # Obtener los criterios originales
                    criterios = self.memory_manager.get_beliefs(session_id).get("criterios", {})
                    
                    # Limpiar tareas de búsqueda existentes (si las hay) para evitar duplicados
                    existing_tasks = self.task_queue[session_id]
                    search_task_types = ["venue_search", "catering_search", "decor_search"]
                    filtered_tasks = [task for task in existing_tasks if task.type not in search_task_types]
                    self.task_queue[session_id] = filtered_tasks
                    
                    print(f"[PlannerAgent] Limpiadas {len(existing_tasks) - len(filtered_tasks)} tareas de búsqueda existentes")
                    
                    # Crear tareas de búsqueda con los presupuestos asignados
                    self._create_search_tasks(session_id, criterios)

        # Procesa la siguiente tarea
        self._process_next_task(session_id)

    def _handle_task_error(self, session_id: str, failed_task: Task, error_content: Any):
        """Maneja errores de tareas con estrategias de corrección inteligentes."""
        print(f"[PlannerAgent] 🚨 Manejando error en tarea {failed_task.type}")
        
        # Obtener beliefs actuales
        beliefs = self.memory_manager.get_beliefs(session_id)
        
        # Registrar el error en los beliefs
        error_history = beliefs.get("error_history", [])
        error_record = {
            "task_type": failed_task.type,
            "error": str(error_content),
            "timestamp": datetime.now().isoformat(),
            "retry_count": failed_task.retry_count if hasattr(failed_task, 'retry_count') else 0
        }
        error_history.append(error_record)
        
        # Actualizar beliefs con el historial de errores
        self.memory_manager.update_beliefs(session_id, {
            "error_history": error_history,
            "last_error": error_record
        })
        
        # Estrategias de corrección basadas en el tipo de tarea
        correction_strategies = self._get_correction_strategies(failed_task.type, error_content)
        
        if correction_strategies:
            print(f"[PlannerAgent] Aplicando estrategias de corrección: {correction_strategies}")
            
            # Crear tareas de corrección
            correction_tasks = self._create_correction_tasks_from_strategies(
                session_id, failed_task, correction_strategies
            )
            
            # Insertar tareas de corrección al inicio de la cola (prioridad alta)
            self.task_queue[session_id] = correction_tasks + self.task_queue[session_id]
            
            # Marcar la tarea original como "retry_pending" en lugar de "error"
            failed_task.status = "retry_pending"
            
        else:
            # Si no hay estrategias de corrección, marcar como error permanente
            failed_task.status = "error"
            failed_task.error = error_content
            print(f"[PlannerAgent] ⚠️ No se encontraron estrategias de corrección para {failed_task.type}")

    def _get_correction_strategies(self, task_type: str, error_content: Any) -> List[Dict[str, Any]]:
        """Obtiene estrategias de corrección basadas en el tipo de tarea y el error."""
        strategies = []
        
        # Usar RAG para obtener estrategias de corrección
        if hasattr(self, 'rag') and self.rag:
            rag_strategies = self.rag.suggest_error_correction(task_type, error_content)
            if rag_strategies:
                strategies.extend(rag_strategies)
        
        # Estrategias específicas por tipo de tarea
        if task_type == "budget_distribution":
            strategies.extend([
                {
                    "type": "budget_adjustment",
                    "description": "Ajustar criterios de presupuesto",
                    "parameters": {"adjustment_factor": 0.9}
                },
                {
                    "type": "budget_redistribution",
                    "description": "Redistribuir presupuesto con restricciones más flexibles",
                    "parameters": {"flexible_constraints": True}
                }
            ])
        
        elif task_type in ["venue_search", "catering_search", "decor_search"]:
            category = task_type.replace("_search", "")
            strategies.extend([
                {
                    "type": f"{category}_relax_constraints",
                    "description": f"Relajar restricciones de {category}",
                    "parameters": {"relax_factor": 0.8}
                },
                {
                    "type": f"{category}_alternative_search",
                    "description": f"Buscar alternativas de {category}",
                    "parameters": {"use_alternatives": True}
                },
                {
                    "type": f"{category}_budget_increase",
                    "description": f"Aumentar presupuesto para {category}",
                    "parameters": {"budget_increase": 0.2}
                }
            ])
        
        return strategies

    def _create_correction_tasks_from_strategies(self, session_id: str, failed_task: Task, strategies: List[Dict[str, Any]]) -> List[Task]:
        """Crea tareas de corrección basadas en las estrategias."""
        correction_tasks = []
        
        for strategy in strategies:
            task_id = str(uuid.uuid4())
            
            # Crear parámetros de corrección
            correction_parameters = failed_task.parameters.copy()
            correction_parameters.update(strategy.get("parameters", {}))
            correction_parameters["correction_strategy"] = strategy
            correction_parameters["original_task_id"] = failed_task.id
            
            # Determinar el tipo de tarea de corrección
            correction_task_type = self._map_correction_strategy_to_task_type(strategy["type"])
            
            correction_task = Task(
                id=task_id,
                type=correction_task_type,
                parameters=correction_parameters,
                status="pending"
            )
            
            correction_tasks.append(correction_task)
            print(f"[PlannerAgent] Creada tarea de corrección: {correction_task_type}")
        
        return correction_tasks

    def _map_correction_strategy_to_task_type(self, strategy_type: str) -> str:
        """Mapea estrategias de corrección a tipos de tarea."""
        strategy_mapping = {
            "budget_adjustment": "budget_distribution",
            "budget_redistribution": "budget_distribution",
            "venue_relax_constraints": "venue_search",
            "venue_alternative_search": "venue_search",
            "venue_budget_increase": "venue_search",
            "catering_relax_constraints": "catering_search",
            "catering_alternative_search": "catering_search",
            "catering_budget_increase": "catering_search",
            "decor_relax_constraints": "decor_search",
            "decor_alternative_search": "decor_search",
            "decor_budget_increase": "decor_search"
        }
        
        return strategy_mapping.get(strategy_type, "unknown_correction")

    def _create_search_tasks(self, session_id: str, criterios: Dict[str, Any]):
        """Crea las tareas de búsqueda basadas en los criterios."""
        tasks = []
        
        print(f"[PlannerAgent] 🔍 Creando tareas de búsqueda para sesión {session_id}")
        
        # Obtener la distribución de presupuesto
        presupuesto_asignado = self.memory_manager.get_beliefs(session_id).get("presupuesto_asignado", {})
        if not presupuesto_asignado:
            print("[PlannerAgent] ⚠️ No se encontró distribución de presupuesto")
            return
            
        # Extraer la distribución real del diccionario
        if isinstance(presupuesto_asignado, dict) and "distribution" in presupuesto_asignado:
            presupuesto_asignado = presupuesto_asignado["distribution"]
        
        print(f"[PlannerAgent] 💰 Presupuestos asignados: {presupuesto_asignado}")
        
        # Crear tareas de búsqueda para cada categoría
        if "venue" in criterios:
            venue_criteria = criterios["venue"].copy()
            venue_criteria["price"] = presupuesto_asignado.get("venue", 0)
            # Mapear campos para RAG
            venue_criteria["budget"] = venue_criteria["price"]
            venue_criteria["guest_count"] = criterios.get("guest_count", 0)
            # Pasar el estilo desde los criterios principales
            venue_criteria["style"] = criterios.get("style", "classic")
            print(f"[PlannerAgent] 🏰 Criterios de venue: {venue_criteria}")
            
            venue_task = Task(
                id=str(uuid.uuid4()),
                type="venue_search",
                parameters=venue_criteria
            )
            tasks.append(venue_task)
            print(f"[PlannerAgent] ✅ Creada tarea venue_search con ID: {venue_task.id}")

        if "catering" in criterios:
            catering_criteria = criterios["catering"].copy()
            catering_criteria["price"] = presupuesto_asignado.get("catering", 0)
            # Mapear campos para RAG
            catering_criteria["budget"] = catering_criteria["price"]
            catering_criteria["guest_count"] = criterios.get("guest_count", 0)
            # Pasar el estilo desde los criterios principales
            catering_criteria["style"] = criterios.get("style", "classic")
            print(f"[PlannerAgent] 🍽️ Criterios de catering: {catering_criteria}")
            
            catering_task = Task(
                id=str(uuid.uuid4()),
                type="catering_search",
                parameters=catering_criteria
            )
            tasks.append(catering_task)
            print(f"[PlannerAgent] ✅ Creada tarea catering_search con ID: {catering_task.id}")

        if "decor" in criterios:
            decor_criteria = criterios["decor"].copy()
            decor_criteria["price"] = presupuesto_asignado.get("decor", 0)
            # Mapear campos para RAG
            decor_criteria["budget"] = decor_criteria["price"]
            decor_criteria["guest_count"] = criterios.get("guest_count", 0)
            # Pasar el estilo desde los criterios principales
            decor_criteria["style"] = criterios.get("style", "classic")
            print(f"[PlannerAgent] 🌸 Criterios de decor: {decor_criteria}")
            
            decor_task = Task(
                id=str(uuid.uuid4()),
                type="decor_search",
                parameters=decor_criteria
            )
            tasks.append(decor_task)
            print(f"[PlannerAgent] ✅ Creada tarea decor_search con ID: {decor_task.id}")

        # Agregar tareas a la cola
        self.task_queue[session_id].extend(tasks)
        print(f"[PlannerAgent] 🎯 Se crearon {len(tasks)} tareas de búsqueda para la sesión {session_id}")
        print(f"[PlannerAgent] 📊 Total de tareas en cola: {len(self.task_queue[session_id])}")
        
        # Mostrar resumen de tareas creadas
        for task in tasks:
            print(f"[PlannerAgent] 📋 Tarea: {task.type} (ID: {task.id[:8]}...) - Presupuesto: ${task.parameters.get('budget', 0):,}")

    def _create_tasks(self, session_id: str, request: Dict[str, Any]):
        """Crea las tareas necesarias basadas en la petición."""
        tasks = []
        criterios = request.get("criterios", {})
        
        # Verificar si ya existe una distribución de presupuesto válida
        needs_budget_distribution = True
        if "presupuesto_total" in criterios:
            # Verificar si cada categoría tiene un presupuesto asignado
            has_valid_distribution = True
            total_assigned = 0
            
            for category in ["venue", "catering", "decor"]:
                if category in criterios and "price" in criterios[category]:
                    total_assigned += criterios[category]["price"]
                else:
                    has_valid_distribution = False
                    break
            
            # Verificar que la suma de los presupuestos asignados sea igual al total
            if has_valid_distribution and total_assigned == criterios["presupuesto_total"]:
                needs_budget_distribution = False
                print(f"[PlannerAgent] Se detectó una distribución de presupuesto válida: {total_assigned}")
        
        # Crear tarea de distribución de presupuesto solo si es necesario
        if needs_budget_distribution and "presupuesto_total" in criterios:
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="budget_distribution",
                parameters={
                    "budget": criterios["presupuesto_total"],
                    "criterios": criterios
                }
            ))
            print("[PlannerAgent] Se creó tarea de distribución de presupuesto")

            # No crear tareas de búsqueda hasta que se complete la distribución
            self.task_queue[session_id].extend(tasks)
            print(f"[PlannerAgent] Se crearon {len(tasks)} tareas para la sesión {session_id}")
            return

        # Si ya tenemos una distribución válida, crear tareas de búsqueda
        self._create_search_tasks(session_id, criterios)

    def _create_correction_tasks(self, session_id: str, affected_elements: List[str], correction: Dict[str, Any]):
        """Crea tareas específicas para una corrección."""
        tasks = []
        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        for element in affected_elements:
            if element == "budget":
                tasks.append(Task(
                    id=str(uuid.uuid4()),
                    type="budget_distribution",
                    parameters={"budget": correction["presupuesto_total"]}
                ))
            elif element in ["venue", "catering", "decor"]:
                tasks.append(Task(
                    id=str(uuid.uuid4()),
                    type=f"{element}_search",
                    parameters=correction.get(element, {})
                ))

        self.task_queue[session_id].extend(tasks)

    def _process_next_task(self, session_id: str):
        """Procesa la siguiente tarea en la cola."""
        if session_id not in self.task_queue or not self.task_queue[session_id]:
            print(f"[PlannerAgent] No hay más tareas pendientes para la sesión {session_id}")
            self._check_completion(session_id)
            return

        task = self.task_queue[session_id].pop(0)
        self.current_task[session_id] = task

        # Determinar el agente objetivo
        target_agent = self._get_target_agent(task.type)
        print(f"[PlannerAgent] Enviando tarea {task.type} al agente {target_agent}")
        
        # Obtener datos compartidos del bus
        shared_data = self.bus.get_shared_data()
        print(f"[PlannerAgent] Datos compartidos disponibles: {list(shared_data.keys())}")
        
        # Envía la tarea al agente correspondiente y espera la respuesta
        message = {
            "origen": self.name,
            "destino": target_agent,
            "tipo": "task",
            "contenido": {
                "task_id": task.id,
                "parameters": task.parameters,
                "graph_data": shared_data  # Incluir todos los datos compartidos
            },
            "session_id": session_id
        }
        
        response = self.bus.send_and_wait(message)
        if response:
            self._handle_agent_response(session_id, response)
        else:
            print(f"[PlannerAgent] ⚠️ No se recibió respuesta para la tarea {task.id}")
            task.status = "error"
            task.error = "Timeout esperando respuesta"
            self._process_next_task(session_id)

    def _get_target_agent(self, task_type: str) -> str:
        """Determina el agente objetivo basado en el tipo de tarea."""
        agent_mapping = {
            "budget_distribution": "BudgetDistributorAgent",
            "venue_search": "VenueAgent",
            "catering_search": "CateringAgent",
            "decor_search": "DecorAgent"
        }
        return agent_mapping.get(task_type, "UnknownAgent")
            
    def _extract_price_value(self, price_data: Any) -> float:
        """Extrae el valor numérico de un precio en diferentes formatos."""
        if isinstance(price_data, (int, float)):
            return float(price_data)
        
        if isinstance(price_data, str):
            # Intentar extraer números del string
            import re
            match = re.search(r'\d+(?:\.\d+)?', price_data)
            if match:
                return float(match.group())
        
        if isinstance(price_data, dict):
            # Si es un diccionario, buscar el valor en diferentes claves comunes
            for key in ["price", "value", "amount", "cost"]:
                if key in price_data:
                    return self._extract_price_value(price_data[key])
            
            # Si no encontramos una clave específica, intentar con el primer valor
            for value in price_data.values():
                try:
                    return self._extract_price_value(value)
                except (ValueError, TypeError):
                    continue
        
        raise ValueError(f"No se pudo extraer un valor numérico de: {price_data}")

    def _filter_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra y simplifica un resultado para incluir solo la información relevante."""
        filtered = {}
        
        # Campos básicos que siempre incluimos
        basic_fields = ["tipo", "nombre", "title", "price", "capacity", "location"]
        for field in basic_fields:
            if field in result:
                filtered[field] = result[field]
        
        # Si hay original_data, extraer campos relevantes
        if "original_data" in result:
            data = result["original_data"]
            for field in basic_fields:
                if field in data and field not in filtered:
                    filtered[field] = data[field]
        
        return filtered
            
    def _check_completion(self, session_id: str):
        """Verifica si todas las tareas están completadas y genera la respuesta final."""
        # Obtener beliefs actualizados del SessionMemoryManager
        beliefs = self.memory_manager.get_beliefs(session_id)

        # Verifica si todas las categorías están completadas
        completado = beliefs.get("completado", {})
        all_completed = all(completado.get(cat, False) for cat in ["venue", "catering", "decor"])

        if all_completed:
            print(f"[PlannerAgent] Todas las tareas completadas para la sesión {session_id}")
            
            # Calcular presupuesto usado
            presupuesto_usado = 0.0
            resultados = {}
            
            # Obtener resultados y calcular presupuesto
            for categoria in ["venue", "catering", "decor"]:
                resultados_categoria = beliefs.get(categoria)
                if resultados_categoria and isinstance(resultados_categoria, list) and len(resultados_categoria) > 0:
                    # Tomar solo el primer resultado
                    primer_resultado = resultados_categoria[0]
                    # Extraer solo los campos relevantes
                    resultado_filtrado = {
                        "tipo": primer_resultado.get("tipo"),
                        "nombre": primer_resultado.get("nombre") or primer_resultado.get("title"),
                        "precio": self._extract_price_value(primer_resultado.get("original_data", {}).get("price", 0)),
                        "capacidad": primer_resultado.get("original_data", {}).get("capacity"),
                        "ubicacion": primer_resultado.get("original_data", {}).get("location")
                    }
                    resultados[categoria] = resultado_filtrado
                    
                    # Actualizar presupuesto usado
                    presupuesto_usado += resultado_filtrado["precio"]
            
            # Actualizar el estado y presupuesto en el SessionMemoryManager
            self.memory_manager.update_beliefs(session_id, {
                "estado": "completado",
                "presupuesto_usado": presupuesto_usado,
                "ultima_actualizacion": datetime.now().isoformat()
            })
            
            # Obtener beliefs actualizados después de los cambios
            beliefs = self.memory_manager.get_beliefs(session_id)
            
            # Genera resumen final
            resumen = beliefs.resumen()
            
            # Envía respuesta al usuario
            response = {
                "origen": self.name,
                "destino": "user",
                "tipo": "final_response",
                "contenido": {
                    "resumen": resumen,
                    "resultados": resultados,
                    "session_id": session_id,
                    "is_correction": self.active_sessions[session_id]["is_correction"]
                },
                "session_id": session_id
                }
            
            print(f"[PlannerAgent] Generando respuesta final: {response}")
            return response
        else:
            print(f"[PlannerAgent] Sesión {session_id} aún no completada. Estado: {completado}")
            return None

    def _identify_affected_elements(self, correction: Dict[str, Any]) -> List[str]:
        """Identifica qué elementos necesitan ser recalculados basado en la corrección."""
        affected = []
        
        if "presupuesto_total" in correction:
            affected.append("budget")
            
        for element in ["venue", "catering", "decor"]:
            if element in correction:
                affected.append(element)
                
        return affected

    def _create_desires_from_request(self, session_id: str, request: Dict[str, Any]) -> List[Desire]:
        """Crea desires basados en la petición del usuario."""
        desires = []
        criterios = request.get("criterios", {})
        
        # Desire principal: completar la planificación del evento
        main_desire = Desire(
            id=str(uuid.uuid4()),
            type="complete_event_planning",
            priority=1.0,
            parameters={
                "event_type": "wedding",
                "guest_count": criterios.get("guest_count", 0),
                "budget": criterios.get("presupuesto_total", 0),
                "style": criterios.get("style", "classic")
            },
            created_at=datetime.now().isoformat()
        )
        desires.append(main_desire)
        
        # Desires específicos por categoría
        if "venue" in criterios:
            venue_desire = Desire(
                id=str(uuid.uuid4()),
                type="find_venue",
                priority=0.9,
                parameters=criterios["venue"],
                created_at=datetime.now().isoformat()
            )
            desires.append(venue_desire)
        
        if "catering" in criterios:
            catering_desire = Desire(
                id=str(uuid.uuid4()),
                type="find_catering",
                priority=0.8,
                parameters=criterios["catering"],
                created_at=datetime.now().isoformat()
            )
            desires.append(catering_desire)
        
        if "decor" in criterios:
            decor_desire = Desire(
                id=str(uuid.uuid4()),
                type="find_decor",
                priority=0.7,
                parameters=criterios["decor"],
                created_at=datetime.now().isoformat()
            )
            desires.append(decor_desire)
        
        return desires

    def _create_intentions_from_desires(self, session_id: str, desires: List[Desire]) -> List[Intention]:
        """Crea intentions basados en los desires activos."""
        intentions = []
        
        print(f"[PlannerAgent] Creando intentions para {len(desires)} desires")
        
        for desire in desires:
            if desire.status == "active":
                print(f"[PlannerAgent] Procesando desire: {desire.type}")
                
                # Crear tareas basadas en el tipo de desire
                tasks = self._create_tasks_for_desire(desire)
                print(f"[PlannerAgent] Creadas {len(tasks)} tareas para desire {desire.type}")
                
                # Crear intention
                intention = Intention(
                    id=str(uuid.uuid4()),
                    desire_id=desire.id,
                    tasks=[task.id for task in tasks],
                    created_at=datetime.now().isoformat()
                )
                intentions.append(intention)
                
                # Agregar tareas a la cola
                if tasks:
                    self.task_queue[session_id].extend(tasks)
                    print(f"[PlannerAgent] Agregadas {len(tasks)} tareas a la cola para sesión {session_id}")
                else:
                    print(f"[PlannerAgent] ⚠️ No se crearon tareas para desire {desire.type}")
        
        print(f"[PlannerAgent] Total de intentions creadas: {len(intentions)}")
        print(f"[PlannerAgent] Total de tareas en cola: {len(self.task_queue[session_id])}")
        
        return intentions

    def _create_tasks_for_desire(self, desire: Desire) -> List[Task]:
        """Crea tareas específicas para un desire."""
        tasks = []
        
        print(f"[PlannerAgent] Creando tareas para desire tipo: {desire.type}")
        print(f"[PlannerAgent] Parámetros del desire: {desire.parameters}")
        
        if desire.type == "complete_event_planning":
            # Tarea de distribución de presupuesto
            budget_task = Task(
                id=str(uuid.uuid4()),
                type="budget_distribution",
                parameters={
                    "budget": desire.parameters.get("budget", 0),
                    "criterios": desire.parameters
                }
            )
            tasks.append(budget_task)
            print(f"[PlannerAgent] Creada tarea budget_distribution con ID: {budget_task.id}")
        
        # NOTA: Las tareas de búsqueda (venue_search, catering_search, decor_search) 
        # NO se crean aquí. Se crearán después de completar la distribución de presupuesto
        # para asegurar que tengan el presupuesto asignado correctamente.
        elif desire.type in ["find_venue", "find_catering", "find_decor"]:
            print(f"[PlannerAgent] ⏳ Tarea de búsqueda {desire.type} será creada después de la distribución de presupuesto")
            # No crear tareas aquí - se crearán después de budget_distribution
        
        else:
            print(f"[PlannerAgent] ⚠️ Tipo de desire no reconocido: {desire.type}")
        
        print(f"[PlannerAgent] Total de tareas creadas para desire {desire.type}: {len(tasks)}")
        return tasks

    def _update_beliefs_from_environment(self, session_id: str):
        """Actualiza beliefs basado en el estado actual del entorno."""
        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]
        
        # Obtener estado actual de tareas
        pending_tasks = len([t for t in self.task_queue[session_id] if t.status == "pending"])
        completed_tasks = len([t for t in self.task_queue[session_id] if t.status == "completed"])
        failed_tasks = len([t for t in self.task_queue[session_id] if t.status == "error"])
        
        # Actualizar beliefs sobre el progreso
        beliefs.set("task_progress", {
            "pending": pending_tasks,
            "completed": completed_tasks,
            "failed": failed_tasks,
            "total": len(self.task_queue[session_id])
        })
        
        # Actualizar beliefs sobre el estado general
        if failed_tasks > 0:
            beliefs.set("system_status", "error_recovery")
        elif pending_tasks == 0 and completed_tasks > 0:
            beliefs.set("system_status", "completed")
        else:
            beliefs.set("system_status", "in_progress")

    def _reconsider_intentions(self, session_id: str):
        """Reconsidera las intentions basado en los beliefs actuales."""
        beliefs = self.memory_manager.get_beliefs(session_id)
        current_intentions = self.intentions.get(session_id, [])
        
        # Verificar si hay errores que requieren reconsideración
        error_history = beliefs.get("error_history", [])
        if error_history:
            last_error = error_history[-1]
            
            # Si hay errores recientes, reconsiderar intentions
            if self._should_reconsider_intentions(last_error):
                print(f"[PlannerAgent] 🔄 Reconsiderando intentions debido a errores")
                
                # Desactivar intentions problemáticas
                for intention in current_intentions:
                    if intention.status == "active":
                        # Verificar si la intention está relacionada con el error
                        if self._intention_related_to_error(intention, last_error):
                            intention.status = "suspended"
                            print(f"[PlannerAgent] Intention {intention.id} suspendida")
                
                # Crear nuevas intentions de corrección
                correction_desires = self._create_correction_desires(session_id, last_error)
                correction_intentions = self._create_intentions_from_desires(session_id, correction_desires)
                self.intentions[session_id].extend(correction_intentions)

    def _should_reconsider_intentions(self, last_error: Dict[str, Any]) -> bool:
        """Determina si se deben reconsiderar las intentions basado en el error."""
        # Reconsiderar si hay errores críticos o múltiples errores
        error_type = last_error.get("task_type", "")
        error_message = str(last_error.get("error", "")).lower()
        
        critical_errors = ["budget_distribution", "timeout", "connection_error"]
        return any(critical in error_type or critical in error_message for critical in critical_errors)

    def _intention_related_to_error(self, intention: Intention, error: Dict[str, Any]) -> bool:
        """Verifica si una intention está relacionada con un error específico."""
        error_task_type = error.get("task_type", "")
        
        # Verificar si alguna tarea de la intention es del mismo tipo que el error
        for task_id in intention.tasks:
            # Buscar la tarea en la cola
            for session_tasks in self.task_queue.values():
                for task in session_tasks:
                    if task.id == task_id and task.type == error_task_type:
                        return True
        
        return False

    def _create_correction_desires(self, session_id: str, error: Dict[str, Any]) -> List[Desire]:
        """Crea desires de corrección basados en el error."""
        correction_desires = []
        error_task_type = error.get("task_type", "")
        
        if error_task_type == "budget_distribution":
            correction_desires.append(Desire(
                id=str(uuid.uuid4()),
                type="fix_budget_distribution",
                priority=0.95,  # Alta prioridad para correcciones
                parameters={"error_context": error},
                created_at=datetime.now().isoformat()
            ))
        
        elif error_task_type in ["venue_search", "catering_search", "decor_search"]:
            category = error_task_type.replace("_search", "")
            correction_desires.append(Desire(
                id=str(uuid.uuid4()),
                type=f"fix_{category}_search",
                priority=0.9,
                parameters={"error_context": error, "category": category},
                created_at=datetime.now().isoformat()
            ))
        
        return correction_desires

class MessageBus:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.listeners = {}  # agente_id -> callback
        self.history = []    # para trazabilidad
        self.response_queue = queue.Queue()  # Cola para respuestas
        self.waiting_responses = {}  # task_id -> (session_id, callback)
        self.shared_data = {}  # Datos compartidos entre agentes

    def set_shared_data(self, key: str, value: Any):
        """Establece un dato compartido en el bus"""
        self.shared_data[key] = value
        print(f"[MessageBus] Dato compartido '{key}' actualizado")

    def get_shared_data(self) -> Dict[str, Any]:
        """Obtiene todos los datos compartidos"""
        return self.shared_data

    def register(self, agent_id: str, callback):
        """Registra una función que escucha mensajes dirigidos a este agente"""
        self.listeners[agent_id] = callback
        print(f"[MessageBus] Agente {agent_id} registrado")

    def send(self, message: Dict[str, Any]):
        """Envía un mensaje al bus"""
        print(f"[MessageBus] Enviando mensaje de {message['origen']} a {message['destino']}")
        self.message_queue.put(message)
        self.history.append(message)

    def send_and_wait(self, message: Dict[str, Any], timeout: int = 30) -> Optional[Dict]:
        """Envía un mensaje y espera la respuesta"""
        if "task_id" not in message["contenido"]:
            print("[MessageBus] ⚠️ Mensaje sin task_id, no se puede esperar respuesta")
            return None

        task_id = message["contenido"]["task_id"]
        session_id = message["session_id"]
        
        # Crear un evento para sincronizar
        response_event = threading.Event()
        response_data = [None]  # Usar lista para poder modificar desde el closure
        
        def response_callback(response):
            print(f"[MessageBus] Respuesta recibida para task {task_id}")
            response_data[0] = response
            response_event.set()
        
        # Registrar el callback para esta tarea
        self.waiting_responses[task_id] = (session_id, response_callback)
        
        # Enviar el mensaje
        self.send(message)
        
        # Esperar la respuesta
        if response_event.wait(timeout):
            return response_data[0]
        else:
            print(f"[MessageBus] ⚠️ Timeout esperando respuesta para task {task_id}")
            # Limpiar el callback para evitar memory leaks
            if task_id in self.waiting_responses:
                del self.waiting_responses[task_id]
            return None

    def broadcast(self, tipo: str, contenido: Any, origen: str, session_id: str):
        """Envía a todos los agentes registrados"""
        for destino in self.listeners:
            self.send({
                "origen": origen,
                "destino": destino,
                "tipo": tipo,
                "contenido": contenido,
                "session_id": session_id
            })

    def start(self):
        """Arranca el loop del bus"""
        print("[MessageBus] Iniciando bus de mensajes...")
        threading.Thread(target=self._loop, daemon=True).start()
        threading.Thread(target=self._response_loop, daemon=True).start()

    def _loop(self):
        """Loop principal del bus de mensajes"""
        while True:
            message = self.message_queue.get()
            destino = message.get("destino")
            
            if destino == "all":
                print(f"[MessageBus] Broadcast a todos los agentes")
                for agente, callback in self.listeners.items():
                    callback(message)
            elif destino in self.listeners:
                print(f"[MessageBus] Procesando mensaje para {destino}")
                # Añadir datos compartidos al mensaje si existen
                if "graph_data" in message["contenido"]:
                    self.shared_data.update(message["contenido"]["graph_data"])
                response = self.listeners[destino](message)
                if response:
                    self.response_queue.put(response)
            else:
                print(f"[MessageBus] ⚠️ Destino no encontrado: {destino}")

    def _response_loop(self):
        """Loop para procesar respuestas"""
        while True:
            try:
                response = self.response_queue.get(timeout=1)  # Timeout de 1 segundo para evitar bloqueo
                if "task_id" in response.get("contenido", {}):
                    task_id = response["contenido"]["task_id"]
                    if task_id in self.waiting_responses:
                        session_id, callback = self.waiting_responses.pop(task_id)
                        callback(response)
                else:
                    print(f"[MessageBus] ⚠️ Respuesta sin task_id: {response}")
            except queue.Empty:
                continue  # Continuar el loop si no hay respuestas
            except Exception as e:
                print(f"[MessageBus] ⚠️ Error procesando respuesta: {str(e)}")