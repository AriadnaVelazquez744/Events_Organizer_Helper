# agents/planner_agent_bdi.py
import queue
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from beliefs_schema import BeliefState
from session_memory import SessionMemoryManager
from planner_rag import PlannerRAG

@dataclass
class Task:
    id: str
    type: str
    parameters: Dict[str, Any]
    status: str = "pending"
    result: Optional[Dict] = None
    error: Optional[str] = None

class PlannerAgentBDI:
    def __init__(self, name: str, bus, memory_manager: SessionMemoryManager):
        self.name = name
        self.bus = bus
        self.memory_manager = memory_manager
        self.active_sessions: Dict[str, Dict] = {}  # session_id -> session_data
        self.task_queue: Dict[str, List[Task]] = {}  # session_id -> [tasks]
        self.current_task: Dict[str, Task] = {}  # session_id -> current_task
        self.rag = PlannerRAG()  # Inicializa el sistema RAG
        
    def create_session(self, user_id: str) -> str:
        """Crea una nueva sesión para un usuario."""
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "beliefs": BeliefState(),
            "is_correction": False,
            "original_session": None,
            "created_at": datetime.now().isoformat()
        }
        self.task_queue[session_id] = []
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
            return

        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        if message["tipo"] == "user_request":
            self._handle_user_request(session_id, message["contenido"])
        elif message["tipo"] == "agent_response":
            self._handle_agent_response(session_id, message)
        elif message["tipo"] == "correction_request":
            self._handle_correction_request(session_id, message["contenido"])

    def _handle_user_request(self, session_id: str, request: Dict[str, Any]):
        """Procesa una nueva petición del usuario."""
        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        # Actualiza criterios
        if "criterios" in request:
            beliefs.set("criterios", request["criterios"])
            
            # Usa RAG para obtener recomendaciones de presupuesto
            if "presupuesto_total" in request["criterios"]:
                budget_distribution = self.rag.get_budget_distribution(
                    request["criterios"]["presupuesto_total"]
                )
                beliefs.set("presupuesto_asignado", budget_distribution)

        # Crea tareas basadas en los criterios
        self._create_tasks(session_id, request)

        # Inicia el procesamiento de tareas
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
            current_task.status = "error"
            current_task.error = message["contenido"]
            
            # Usa RAG para obtener estrategias de resolución de errores
            strategies = self.rag.suggest_conflict_resolution(
                "error_agente",
                {
                    "task_type": current_task.type,
                    "error": message["contenido"]
                }
            )
            if strategies:
                session = self.active_sessions[session_id]
                session["beliefs"].set("estrategias_error", strategies)
        else:
            current_task.status = "completed"
            current_task.result = message["contenido"]
            
            # Actualiza beliefs con el resultado
            session = self.active_sessions[session_id]
            beliefs = session["beliefs"]
            
            # Mapeo de tipos de tarea a claves de belief
            task_to_belief = {
                "budget_distribution": "presupuesto_asignado",
                "venue_search": "venue",
                "catering_search": "catering",
                "decor_search": "decor"
            }
            
            belief_key = task_to_belief.get(current_task.type)
            if belief_key:
                beliefs.set(belief_key, message["contenido"])
                
                # Actualiza patrones de éxito en RAG
                self.rag.update_success_pattern(
                    "vendor_selection",
                    {
                        "type": current_task.type,
                        "result": message["contenido"],
                        "parameters": current_task.parameters
                    }
                )
            else:
                print(f"[⚠️] Tipo de tarea no mapeado: {current_task.type}")

        # Verifica si hay más tareas pendientes
        self._process_next_task(session_id)

    def _create_tasks(self, session_id: str, request: Dict[str, Any]):
        """Crea las tareas necesarias basadas en la petición."""
        tasks = []
        criterios = request.get("criterios", {})

        # Tarea de distribución de presupuesto
        if "presupuesto_total" in criterios:
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="budget_distribution",
                parameters={"budget": criterios["presupuesto_total"]}
            ))

        # Tareas de búsqueda de servicios
        if "venue" in criterios:
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="venue_search",
                parameters=criterios["venue"]
            ))

        if "catering" in criterios:
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="catering_search",
                parameters=criterios["catering"]
            ))

        if "decor" in criterios:
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="decor_search",
                parameters=criterios["decor"]
            ))

        self.task_queue[session_id].extend(tasks)

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
            self._check_completion(session_id)
            return

        task = self.task_queue[session_id].pop(0)
        self.current_task[session_id] = task

        # Determina el agente objetivo basado en el tipo de tarea
        target_agent = self._get_target_agent(task.type)
        
        # Envía la tarea al agente correspondiente
        self.bus.send({
            "origen": self.name,
            "destino": target_agent,
            "tipo": "task",
            "contenido": {
                "task_id": task.id,
                "parameters": task.parameters
            },
            "session_id": session_id
        })

    def _get_target_agent(self, task_type: str) -> str:
        """Determina el agente objetivo basado en el tipo de tarea."""
        agent_mapping = {
            "budget_distribution": "BudgetDistributorAgent",
            "venue_search": "VenueAgent",
            "catering_search": "CateringAgent",
            "decor_search": "DecorAgent"
        }
        return agent_mapping.get(task_type, "UnknownAgent")
            
    def _check_completion(self, session_id: str):
        """Verifica si todas las tareas están completadas y genera la respuesta final."""
        session = self.active_sessions[session_id]
        beliefs = session["beliefs"]

        if beliefs.is_completo():
            # Genera resumen final
            resumen = beliefs.resumen()
            
            # Envía respuesta al usuario
            self.bus.send({
                "origen": self.name,
                "destino": "user",
                "tipo": "final_response",
                "contenido": {
                    "resumen": resumen,
                    "session_id": session_id,
                    "is_correction": session["is_correction"]
                }
            })

    def _identify_affected_elements(self, correction: Dict[str, Any]) -> List[str]:
        """Identifica qué elementos necesitan ser recalculados basado en la corrección."""
        affected = []
        
        if "presupuesto_total" in correction:
            affected.append("budget")
            
        for element in ["venue", "catering", "decor"]:
            if element in correction:
                affected.append(element)
                
        return affected

class MessageBus:
    def __init__(self):
        self.message_queue = queue.Queue()
        self.listeners = {}  # agente_id -> callback
        self.history = []    # para trazabilidad

    def register(self, agent_id: str, callback):
        """Registra una función que escucha mensajes dirigidos a este agente"""
        self.listeners[agent_id] = callback

    def send(self, message: Dict[str, Any]):
        """Envía un mensaje al bus"""
        self.message_queue.put(message)
        self.history.append(message)

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
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        """Loop principal del bus de mensajes"""
        while True:
            message = self.message_queue.get()
            destino = message.get("destino")
            
            if destino == "all":
                for agente, callback in self.listeners.items():
                    callback(message)
            elif destino in self.listeners:
                self.listeners[destino](message)