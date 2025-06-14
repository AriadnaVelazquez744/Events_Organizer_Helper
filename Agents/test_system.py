import json
from datetime import datetime
from Planneragent import PlannerAgentBDI, MessageBus
from session_memory import SessionMemoryManager
from beliefs_schema import BeliefState, Conflict
from llm_formatter import (
    generar_resumen_natural,
    formatear_correccion,
    formatear_conflicto,
    formatear_presupuesto
)

def test_belief_state():
    """Prueba el funcionamiento del BeliefState."""
    print("\n=== Probando BeliefState ===")
    beliefs = BeliefState()
    
    # Prueba de actualización de criterios
    criterios = {
        "presupuesto_total": 50000,
        "fecha": "2024-12-15",
        "invitados": 100,
        "venue": {
            "capacidad_min": 80,
            "capacidad_max": 120,
            "ubicacion": "Ciudad de México"
        },
        "catering": {
            "tipo": "buffet",
            "dietas": ["vegetariano", "vegano", "sin gluten"]
        },
        "decor": {
            "estilo": "moderno",
            "colores": ["blanco", "dorado"]
        }
    }
    
    beliefs.set("criterios", criterios)
    print("Criterios establecidos:", json.dumps(beliefs.get("criterios"), indent=2))
    
    # Prueba de conflicto
    conflicto = Conflict(
        tipo="presupuesto",
        descripcion="El presupuesto asignado excede el total disponible",
        elementos_afectados=["venue", "catering"],
        severidad="error"
    )
    beliefs.append_conflicto(conflicto)
    print("\nConflicto añadido:", beliefs.has_conflicto("presupuesto"))
    
    # Prueba de resumen
    print("\nResumen del estado:", json.dumps(beliefs.resumen(), indent=2))

def test_session_memory():
    """Prueba el funcionamiento del SessionMemoryManager."""
    print("\n=== Probando SessionMemoryManager ===")
    memory = SessionMemoryManager("test_sessions.json")
    
    # Crear sesión
    session_id = memory.create_session("usuario_test")
    print(f"Sesión creada: {session_id}")
    
    # Obtener beliefs
    beliefs = memory.get_beliefs(session_id)
    print("\nBeliefs iniciales:", json.dumps(beliefs.to_dict(), indent=2))
    
    # Actualizar beliefs
    memory.update_beliefs(session_id, {
        "criterios": {
            "presupuesto_total": 50000,
            "fecha": "2024-12-15"
        }
    })
    
    # Verificar actualización
    updated_beliefs = memory.get_beliefs(session_id)
    print("\nBeliefs actualizados:", json.dumps(updated_beliefs.to_dict(), indent=2))
    
    # Listar sesiones activas
    print("\nSesiones activas:", json.dumps(memory.list_active_sessions(), indent=2))

def test_llm_formatter():
    """Prueba el funcionamiento del LLM Formatter."""
    print("\n=== Probando LLM Formatter ===")
    
    # Prueba de resumen
    resumen = {
        "completado": {
            "venue": True,
            "catering": False,
            "decor": True
        },
        "conflictos": 1,
        "presupuesto_usado": 35000,
        "estado": "en_progreso"
    }
    print("\nResumen formateado:", generar_resumen_natural(resumen))
    
    # Prueba de corrección
    correccion = {
        "tipo": "presupuesto",
        "valor_anterior": 50000,
        "valor_nuevo": 45000,
        "razon": "Ajuste por restricciones financieras"
    }
    print("\nCorrección formateada:", formatear_correccion(correccion))
    
    # Prueba de conflicto
    conflicto = {
        "tipo": "capacidad",
        "descripcion": "La capacidad del venue no cumple con los requisitos",
        "elementos_afectados": ["venue"],
        "severidad": "error"
    }
    print("\nConflicto formateado:", formatear_conflicto(conflicto))
    
    # Prueba de presupuesto
    presupuesto = {
        "total": 50000,
        "distribucion": {
            "venue": 20000,
            "catering": 20000,
            "decor": 10000
        }
    }
    print("\nPresupuesto formateado:", formatear_presupuesto(presupuesto))

def test_planner_agent():
    """Prueba el funcionamiento del PlannerAgent."""
    print("\n=== Probando PlannerAgent ===")
    
    # Crear bus de mensajes y memory manager
    bus = MessageBus()
    memory = SessionMemoryManager("test_sessions.json")
    
    # Crear agente
    planner = PlannerAgentBDI("PlannerAgent", bus, memory)
    
    # Crear sesión
    session_id = planner.create_session("usuario_test")
    print(f"Sesión creada: {session_id}")
    
    # Simular petición de usuario
    user_request = {
        "tipo": "user_request",
        "contenido": {
            "criterios": {
                "presupuesto_total": 50000,
                "fecha": "2024-12-15",
                "invitados": 100
            }
        },
        "session_id": session_id
    }
    
    print("\nProcesando petición de usuario...")
    planner.receive(user_request)
    
    # Simular respuesta de agente
    agent_response = {
        "tipo": "agent_response",
        "contenido": {
            "venue": {
                "nombre": "Salón Ejemplo",
                "capacidad": 120,
                "precio": 20000
            }
        },
        "session_id": session_id
    }
    
    print("\nProcesando respuesta de agente...")
    planner.receive(agent_response)

def main():
    """Función principal que ejecuta todas las pruebas."""
    print("Iniciando pruebas del sistema...")
    
    try:
        test_belief_state()
        test_session_memory()
        test_llm_formatter()
        test_planner_agent()
        print("\n✅ Todas las pruebas completadas exitosamente")
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {str(e)}")

if __name__ == "__main__":
    main() 