# agents/planner_agent_bdi.py
import queue
import threading
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from Agents.beliefs_schema import BeliefState
from Agents.session_memory import SessionMemoryManager
from Agents.planner_rag import PlannerRAG

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
                
                # Actualizar beliefs en el SessionMemoryManager
                self.memory_manager.update_beliefs(session_id, {
                    "criterios": request["criterios"],
                    "presupuesto_asignado": budget_distribution
                })

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
            print(f"[PlannerAgent] Error en tarea {current_task.type}: {message['contenido']}")
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
                    # Crear tareas de búsqueda con los presupuestos asignados
                    self._create_search_tasks(session_id, criterios)

        # Procesa la siguiente tarea
        self._process_next_task(session_id)

    def _create_search_tasks(self, session_id: str, criterios: Dict[str, Any]):
        """Crea las tareas de búsqueda basadas en los criterios."""
        tasks = []
        
        # Obtener la distribución de presupuesto
        presupuesto_asignado = self.memory_manager.get_beliefs(session_id).get("presupuesto_asignado", {})
        if not presupuesto_asignado:
            print("[PlannerAgent] ⚠️ No se encontró distribución de presupuesto")
            return
            
        # Extraer la distribución real del diccionario
        if isinstance(presupuesto_asignado, dict) and "distribution" in presupuesto_asignado:
            presupuesto_asignado = presupuesto_asignado["distribution"]
        
        print(f"[PlannerAgent] Presupuestos asignados: {presupuesto_asignado}")
        
        # Crear tareas de búsqueda para cada categoría
        if "venue" in criterios:
            venue_criteria = criterios["venue"].copy()
            venue_criteria["price"] = presupuesto_asignado.get("venue", 0)
            # Mapear campos para RAG
            venue_criteria["budget"] = venue_criteria["price"]
            venue_criteria["guest_count"] = criterios.get("guest_count", 0)
            print(f"[PlannerAgent] Criterios de venue: {venue_criteria}")
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="venue_search",
                parameters=venue_criteria
            ))

        if "catering" in criterios:
            catering_criteria = criterios["catering"].copy()
            catering_criteria["price"] = presupuesto_asignado.get("catering", 0)
            # Mapear campos para RAG
            catering_criteria["budget"] = catering_criteria["price"]
            catering_criteria["guest_count"] = criterios.get("guest_count", 0)
            print(f"[PlannerAgent] Criterios de catering: {catering_criteria}")
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="catering_search",
                parameters=catering_criteria
            ))

        if "decor" in criterios:
            decor_criteria = criterios["decor"].copy()
            decor_criteria["price"] = presupuesto_asignado.get("decor", 0)
            # Mapear campos para RAG
            decor_criteria["budget"] = decor_criteria["price"]
            decor_criteria["guest_count"] = criterios.get("guest_count", 0)
            print(f"[PlannerAgent] Criterios de decor: {decor_criteria}")
            tasks.append(Task(
                id=str(uuid.uuid4()),
                type="decor_search",
                parameters=decor_criteria
            ))

        self.task_queue[session_id].extend(tasks)
        print(f"[PlannerAgent] Se crearon {len(tasks)} tareas de búsqueda para la sesión {session_id}")
        print(f"[PlannerAgent] Presupuestos asignados: {presupuesto_asignado}")

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