
class PlannerAgentBDI:
    def __init__(self, name, bus):
        self.name = name
        self.bus = bus
        self.beliefs = {}         # conocimiento del mundo actual
        self.desires = []         # metas deseadas
        self.intenciones = []     # planes seleccionados para ejecutar

    def update_beliefs(self, message):
        """Recibe mensajes del bus y actualiza las creencias internas"""
        if "tipo" in message and "contenido" in message:
            self.beliefs[message["tipo"]] = message["contenido"]

    def revise_desires(self):
        """Identifica deseos nuevos en base a lo que falta"""
        deseos = []

        if "venue" not in self.beliefs:
            deseos.append("encontrar_venue")
        if "catering" not in self.beliefs:
            deseos.append("encontrar_catering")
        if "decor" not in self.beliefs:
            deseos.append("encontrar_pastel")

        self.desires = deseos

    def filter_intentions(self):
        """Convierte deseos en intenciones (funciones ejecutables)"""
        intenciones = []

        for deseo in self.desires:
            if deseo == "encontrar_venue":
                def plan():
                    self.bus.send(self.name, "venue_agent", {
                        "accion": "buscar_venue",
                        "criterios": self.beliefs.get("criterios_usuario", {})
                    })
                intenciones.append(plan)

            elif deseo == "encontrar_catering":
                def plan():
                    self.bus.send(self.name, "catering_agent", {
                        "accion": "buscar_catering",
                        "criterios": self.beliefs.get("criterios_usuario", {})
                    })
                intenciones.append(plan)

            elif deseo == "encontrar_pastel":
                def plan():
                    self.bus.send(self.name, "cake_agent", {
                        "accion": "buscar_pastel",
                        "criterios": self.beliefs.get("criterios_usuario", {})
                    })
                intenciones.append(plan)

        self.intenciones = intenciones

    def resolve_conflicts(self):
        """Detecta y resuelve conflictos entre componentes del plan"""
        venue = self.beliefs.get("venue")
        catering = self.beliefs.get("catering")
        criterios = self.beliefs.get("criterios_usuario", {})

        conflictos = []

        if venue and catering:
            restricciones = venue["original_data"].get("restricciones", [])
            texto = " ".join([r.lower() for r in restricciones])
            catering_tipo = catering.get("tipo", "").lower()

            if "no catering externo" in texto or "solo catering interno" in texto:
                if catering_tipo == "externo":
                    if criterios.get("catering"):
                        conflictos.append({
                            "tipo": "conflicto_catering",
                            "mensaje": f"Venue '{venue['nombre']}' no permite catering externo pero el usuario tiene requerimientos de catering.",
                            "accion_recomendada": "cambiar_venue"
                        })

        return conflictos

    def replan_venue(self):
        def plan():
            nuevos_criterios = dict(self.beliefs.get("criterios_usuario", {}))
            nuevos_criterios["restricciones_excluidas"] = ["no catering externo", "solo catering interno"]
            self.bus.send(self.name, "venue_agent", {
                "accion": "buscar_venue",
                "criterios": nuevos_criterios
            })
        return plan

    def act(self):
        """Ejecuta intenciones en orden"""
        for intencion in self.intenciones:
            intencion()
        self.intenciones = []

    def step(self):
        """Un ciclo de razonamiento del agente"""
        message = self.bus.get_for(self.name)
        if message:
            self.update_beliefs(message)
            self.revise_desires()
            self.filter_intentions()
            self.act()

            conflictos = self.resolve_conflicts()
            if conflictos:
                for c in conflictos:
                    print(f"[CONFLICTO] {c['mensaje']}")
                    if c["accion_recomendada"] == "cambiar_venue":
                        self.intenciones.append(self.replan_venue())


class MessageBus:
    def __init__(self):
        self.queue = []

    def send(self, origen, destino, contenido):
        self.queue.append({
            "agente_origen": origen,
            "agente_objetivo": destino,
            "contenido": contenido
        })

    def get_for(self, agente_nombre):
        for i, m in enumerate(self.queue):
            if m["agente_objetivo"] == agente_nombre:
                return self.queue.pop(i)["contenido"]
        return None
