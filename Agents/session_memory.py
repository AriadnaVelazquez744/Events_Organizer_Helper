import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional
from collections import defaultdict
from beliefs_schema import BeliefState

class SessionMemoryManager:
    def __init__(self, storage_file: str = "session_memory.json"):
        self.sessions: Dict[str, Dict] = defaultdict(dict)
        self.storage_file = storage_file
        self._load_from_storage()

    def _load_from_storage(self) -> None:
        """Carga las sesiones desde el archivo de almacenamiento."""
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
                for session_id, session_data in data.items():
                    self.sessions[session_id] = session_data
        except FileNotFoundError:
            pass

    def _save_to_storage(self) -> None:
        """Guarda las sesiones en el archivo de almacenamiento."""
        with open(self.storage_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)

    def create_session(self, user_id: str) -> str:
        """Crea una nueva sesión para un usuario."""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "user_id": user_id,
            "beliefs": BeliefState().to_dict(),
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "status": "active"
        }
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
