import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
from src.agents.beliefs_schema import BeliefState

class SessionMemoryManager:
    def __init__(self, storage_file: str = "session_memory.json"):
        self.sessions: Dict[str, Dict] = defaultdict(dict)
        self.storage_file = storage_file
        self._used_user_ids: set = set()  # Cache for existing user IDs
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Carga las sesiones desde el archivo de almacenamiento."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for session_id, session_data in data.items():
                    self.sessions[session_id] = session_data
                    # Populate the cache with existing user IDs
                    if "user_id" in session_data:
                        self._used_user_ids.add(session_data["user_id"])
        except FileNotFoundError:
            pass

    def _save_to_storage(self) -> None:
        """Guarda las sesiones en el archivo de almacenamiento."""
        with open(self.storage_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)

    def create_session(self, user_id: str, session_id: Optional[str] = None) -> str:
        """Crea una nueva sesión para un usuario."""
        if session_id is None:
            session_id = str(uuid.uuid4())
            
        self.sessions[session_id] = {
            "user_id": user_id,
            "beliefs": BeliefState().to_dict(),
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "status": "active"
        }
        # Add to cache
        self._used_user_ids.add(user_id)
        self._save_to_storage()
        return session_id

    def get_beliefs(self, session_id: str) -> BeliefState:
        """Obtiene los beliefs de una sesión."""
        if session_id not in self.sessions:
            raise KeyError(f"Sesión no encontrada: {session_id}")
        
        session_data = self.sessions[session_id]
        session_data["last_activity"] = datetime.now().isoformat()
        self._save_to_storage()
        
        return BeliefState.from_dict(session_data["beliefs"])

    def update_beliefs(self, session_id: str, updates: Dict[str, Any]) -> None:
        """Actualiza los beliefs de una sesión."""
        if session_id not in self.sessions:
            raise KeyError(f"Sesión no encontrada: {session_id}")
        
        session_data = self.sessions[session_id]
        beliefs = BeliefState.from_dict(session_data["beliefs"])
        
        for key, value in updates.items():
            if isinstance(value, dict) and key in ["completado"]:
                # Handle nested updates for completion status
                for subkey, subvalue in value.items():
                    beliefs.update(key, subkey, subvalue)
            else:
                # Handle direct belief updates
                beliefs.set(key, value)
        
        session_data["beliefs"] = beliefs.to_dict()
        session_data["last_activity"] = datetime.now().isoformat()
        self._save_to_storage()

    def clear_session(self, session_id: str) -> None:
        """Limpia una sesión manteniendo su ID."""
        if session_id in self.sessions:
            self.sessions[session_id] = {
                "user_id": self.sessions[session_id]["user_id"],
                "beliefs": BeliefState().to_dict(),
                "created_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat(),
                "status": "active"
            }
            self._save_to_storage()

    def remove_session(self, session_id: str) -> None:
        """Elimina una sesión completamente."""
        if session_id in self.sessions:
            # Remove from cache
            user_id = self.sessions[session_id].get("user_id")
            if user_id:
                self._used_user_ids.discard(user_id)
            del self.sessions[session_id]
            self._save_to_storage()

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Obtiene información sobre una sesión."""
        if session_id not in self.sessions:
            raise KeyError(f"Sesión no encontrada: {session_id}")
        
        session_data = self.sessions[session_id]
        return {
            "user_id": session_data["user_id"],
            "created_at": session_data["created_at"],
            "last_activity": session_data["last_activity"],
            "status": session_data["status"]
        }

    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Lista todas las sesiones activas."""
        return {
            session_id: self.get_session_info(session_id)
            for session_id, session_data in self.sessions.items()
            if session_data["status"] == "active"
        }

    def archive_session(self, session_id: str) -> None:
        """Archiva una sesión en lugar de eliminarla."""
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "archived"
            self.sessions[session_id]["archived_at"] = datetime.now().isoformat()
            self._save_to_storage()

    def set_all_sessions_inactive(self) -> None:
        """Establece todas las sesiones existentes como inactivas."""
        for session_id in self.sessions:
            self.sessions[session_id]["status"] = "inactive"
            self.sessions[session_id]["inactivated_at"] = datetime.now().isoformat()
        self._save_to_storage()

    def generate_unique_user_id(self) -> str:
        """Genera un user_id único que no existe en ninguna sesión actual."""
        # With UUID4, collisions are extremely rare (1 in 2^122)
        # Try a few times before falling back to counter-based approach
        for _ in range(5):
            new_user_id = f"user_{uuid.uuid4().hex[:8]}"
            if new_user_id not in self._used_user_ids:
                return new_user_id
        
        # Fallback: counter-based approach for extremely rare collision cases
        counter = 1
        while True:
            new_user_id = f"user_{uuid.uuid4().hex[:6]}_{counter:04d}"
            if new_user_id not in self._used_user_ids:
                return new_user_id
            counter += 1
            
    def set_session_status(self, session_id: str, status: str) -> None:
        """Cambia el estado de una sesión.
        
        Args:
            session_id: ID de la sesión a modificar
            status: Nuevo estado para la sesión ('active', 'inactive', 'archived')
            
        Raises:
            KeyError: Si la sesión no existe
            ValueError: Si el estado proporcionado no es válido
        """
        if session_id not in self.sessions:
            raise KeyError(f"Sesión no encontrada: {session_id}")
            
        valid_statuses = ['active', 'inactive', 'archived']
        if status not in valid_statuses:
            raise ValueError(f"Estado inválido. Debe ser uno de: {', '.join(valid_statuses)}")
        
        self.sessions[session_id]["status"] = status
        self.sessions[session_id]["last_activity"] = datetime.now().isoformat()
        
        if status == "inactive":
            self.sessions[session_id]["inactivated_at"] = datetime.now().isoformat()
        elif status == "archived":
            self.sessions[session_id]["archived_at"] = datetime.now().isoformat()
            
        self._save_to_storage()

