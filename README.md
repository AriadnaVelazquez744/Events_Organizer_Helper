# Wedding Organizer: Sistema Inteligente de Planificación de Bodas

## Descripción General

**Wedding Organizer** es un sistema multi-agente inteligente para la planificación automatizada de eventos sociales, especializado en bodas. El sistema implementa una arquitectura BDI (Beliefs-Desires-Intentions) como núcleo de decisión, integrando agentes especializados y técnicas de Retrieval-Augmented Generation (RAG) para ofrecer recomendaciones personalizadas en la selección de venue, catering y decoración.

El proyecto está desarrollado y mantenido por:

- **Lia S. López Rosales**
- **Ariadna Velázquez Rey**

> **Nota:** Este repositorio no cuenta con licencia de uso actualmente.

---

## Principales Características

- **Arquitectura Multi-Agente:**
  - Agente principal BDI (PlannerAgent) que coordina el ciclo de planificación.
  - Agentes especializados: VenueAgent, CateringAgent, DecorAgent, BudgetDistributorAgent.
- **Sistema RAG Integrado:**
  - Grafos de conocimiento por dominio.
  - Recuperación semántica y generación contextual de recomendaciones.
- **Crawler Inteligente:**
  - Enriquecimiento dinámico de datos y validación automática de calidad.
- **Gestión de Memoria y Estado:**
  - Persistencia de creencias, historial de decisiones y recuperación ante fallos.
- **Interfaz Web Moderna:**
  - Basada en Streamlit, con chat interactivo y panel de control para usuarios.

---

## Estructura del Proyecto

```
Events_Organizer_Helper/
├── Agents/                # Implementación de agentes BDI y RAG
├── Crawler/               # Crawlers, enriquecimiento y validación de datos
├── views/                 # Interfaz web (Streamlit)
├── experiment_results/    # Resultados y reportes de experimentos
├── Informe/               # Informe académico y archivos LaTeX
├── requirements.txt       # Dependencias principales
├── requirements_experiments.txt # Dependencias para experimentos
├── pyproject.toml         # Configuración de entorno y dependencias (uv)
└── ...
```

---

## Instalación y Entorno

Este proyecto utiliza el gestor de entornos **[uv](https://github.com/astral-sh/uv)**, que permite una gestión rápida y eficiente de dependencias y entornos virtuales para Python.

### Requisitos previos

- Python 3.12 o superior
- [uv](https://github.com/astral-sh/uv) instalado (`pip install uv`)

### Instalación de dependencias

1. **Clona el repositorio:**

    ```bash
   git clone https://github.com/AriadnaVelazquez744/Events_Organizer_Helper.git
   cd Events_Organizer_Helper
   ```

2. **Crea el entorno y instala dependencias principales:**

   ```bash
   uv .init
   uv add -r requirements.txt
   ```

3. **(Opcional) Instala dependencias para experimentos:**

   ```bash
   uv add -r requirements_experiments.txt
   ```

---

## Ejecución de la Aplicación

La interfaz principal está desarrollada en Streamlit. Para ejecutarla:

```bash
uv add streamlit  # Si no está instalado
streamlit run views/app.py
```

Esto abrirá la aplicación en tu navegador, donde podrás interactuar con el asistente de planificación de eventos.

---

## Uso Básico

- Desde la página principal, haz clic en "Start Planning" para comenzar.
- Describe tus necesidades (tipo de evento, número de invitados, presupuesto, preferencias).
- El sistema te guiará a través de recomendaciones y ajustes personalizados.
- Puedes gestionar tu sesión, agregar presupuesto y reiniciar la planificación desde la barra lateral.

---

## Resultados Experimentales y Evaluación

El sistema fue evaluado mediante una suite de experimentos estadísticos automatizados, con los siguientes resultados destacados:

- **Tasa de Significancia Global:** 63.2% (12 de 19 análisis con resultados significativos)
- **Potencia Promedio:** 0.640 (buena capacidad para detectar efectos reales)
- **Tamaño de Efecto Promedio:** 0.285 (efecto medio)
- **Precisión de Recomendaciones RAG:** 78.5%
- **Tiempo de Respuesta Promedio:** 2.3 segundos por recomendación

### Detalle por Experimento

- **Efectividad del sistema BDI:**
  - 50% de los análisis significativos.
  - Correlaciones muy fuertes entre ciclo BDI y éxito de planificación (p < 0.001).
  - Áreas de mejora: reconsideración dinámica de intenciones.
- **Precisión de sistemas RAG:**
  - 60% de los análisis significativos.
  - Alta precisión en recomendaciones por tipo (venue, catering, decor).
  - Áreas de mejora: adaptabilidad a patrones complejos y consultas atípicas.
- **Rendimiento del sistema:**
  - 100% de los análisis significativos.
  - Excelente escalabilidad, eficiencia y uso de recursos bajo diferentes cargas.
  - Todas las métricas de rendimiento superaron expectativas.
- **Efectividad de integración de componentes:**
  - 40% de los análisis significativos.
  - Buena coordinación entre agentes y robustez del MessageBus.
  - Áreas de mejora: optimización de flujos de comunicación y persistencia de memoria.

> Para más detalles, consulta los reportes en `experiment_results/` y el informe académico en `Informe/`.

---

## Limitaciones y Futuro

- **Limitaciones técnicas:**
  - Escalabilidad de datos limitada (requiere optimización para grandes volúmenes).
  - Latencia de comunicación entre agentes mejorable.
  - Precisión RAG aceptable pero susceptible de mejora.
- **Limitaciones funcionales:**
  - Cobertura centrada en bodas (extensible a otros eventos).
  - Algoritmos de personalización en desarrollo.

### Propuestas de mejora

- Optimización y aumento de la base de datos.
- Paralelización de búsquedas y procesamiento.
- Integración de algoritmos de Machine Learning y análisis de sentimientos.
- Expansión a otros tipos de eventos (corporativos, sociales).

---

## Contribución

Este proyecto es mantenido por dos contribuidoras principales. Si deseas colaborar, abre un issue o pull request.

---

## Referencias

- Arquitectura BDI: Rao & Georgeff (1995), Wooldridge (2009)
- RAG: Lewis et al. (2020)
- Multi-Agente: Ferber (1999)

---

## Contacto

Para dudas o sugerencias, puedes contactarnos a través de [nuestro repositorio en GitHub](https://github.com/AriadnaVelazquez744/Events_Organizer_Helper.git).
