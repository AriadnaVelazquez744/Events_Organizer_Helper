import json
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

from experiments.framework.experimental_framework import (
    BaseExperiment,
    ExperimentConfig,
    ExperimentResult,
    EffectSizeCalculator,
)

class GoldenSetValidationExperiment(BaseExperiment):
    """
    Evalúa el rendimiento del sistema utilizando un "golden set" de consultas.
    Compara los resultados con y sin el uso de un sistema RAG (simulado) para
    medir la mejora en la calidad de la planificacion.
    """

    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any], output_dir: str = None):
        super().__init__(config, system_components, output_dir)
        self.golden_set = self._load_golden_set()
        self.results_data = []
        self.effect_size_calculator = EffectSizeCalculator()

    def _load_golden_set(self) -> List[Dict[str, Any]]:
        """Carga el conjunto de datos de prueba desde el archivo JSON."""
        try:
            with open("experiments/test_data/golden_set_queries.json", "r") as f:
                data = json.load(f)
            print(f"Golden set cargado con {len(data['golden_test_set'])} queries.")
            return data["golden_test_set"]
        except FileNotFoundError:
            print("Error: No se encontró el archivo golden_set_queries.json.")
            return []
        except json.JSONDecodeError as e:
            print(f"Error al decodificar el archivo JSON: {e}")
            return []

    def run(self) -> List[ExperimentResult]:
        if not self.golden_set:
            return []
        
        print("Iniciando experimento de validación con Golden Set...")
        
        for i, query_data in enumerate(self.golden_set):
            query_id = query_data["query_id"]
            criterios = query_data["criterios"]
            difficulty = query_data["difficulty"]

            print(f"Procesando query {i+1}/{len(self.golden_set)}: {query_id} (Dificultad: {difficulty})")

            # Ejecutar sin RAG
            result_no_rag = self._run_single_query(criterios, use_rag=False)
            
            # Ejecutar con RAG
            result_rag = self._run_single_query(criterios, use_rag=True)

            # Evaluar y almacenar resultados
            metrics = self._evaluate_comparison(criterios, result_no_rag, result_rag)
            
            self.results_data.append({
                "query_id": query_id,
                "difficulty": difficulty,
                "criterios": self._serialize_data_for_json(criterios),
                "output_no_rag": self._serialize_data_for_json(result_no_rag),
                "output_rag": self._serialize_data_for_json(result_rag),
                **metrics
            })
            time.sleep(0.5)

        self.save_data("golden_set_validation_results")
        self.generate_visualizations()
        
        return self._analyze_results()

    def _run_single_query(self, criterios: Dict[str, Any], use_rag: bool) -> Dict[str, Any]:
        """Ejecuta una única consulta en el sistema y espera el resultado."""
        planner = self.system_components.get("planner")
        memory = self.system_components.get("memory")

        if not planner or not memory:
            return {"error": "Componentes del sistema no encontrados"}

        user_id = f"user_golden_{int(time.time()*1000)}"
        session_id = planner.create_session(user_id=user_id)

        request_content = {"criterios": criterios}
        
        planner.receive({
            "origen": "experiment",
            "destino": "PlannerAgent",
            "tipo": "user_request",
            "contenido": request_content,
            "session_id": session_id,
            "use_rag": use_rag
        })

        max_wait_time = 120
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            session_info = memory.get_session_info(session_id)
            if session_info and session_info.get("status") in ["completed", "failed"]:
                return session_info.get("final_plan", {"error": "Plan no encontrado en la sesión"})
            time.sleep(2)
            
        return {"error": "Timeout esperando el plan"}

    def _evaluate_comparison(self, criterios: Dict, result_no_rag: Dict, result_rag: Dict) -> Dict[str, Any]:
        """Calcula métricas de calidad comparando los dos resultados."""
        quality_no_rag, details_no_rag = self._calculate_quality_score(criterios, result_no_rag)
        quality_rag, details_rag = self._calculate_quality_score(criterios, result_rag)
        
        metrics = {
            "quality_score_no_rag": quality_no_rag,
            "quality_score_rag": quality_rag,
            "improvement": quality_rag - quality_no_rag,
            "details_no_rag": details_no_rag,
            "details_rag": details_rag
        }
        return metrics

    def _calculate_quality_score(self, criterios: Dict, result: Dict) -> Tuple[float, Dict[str, float]]:
        """Asigna una puntuación de calidad a un único resultado de planificación."""
        if not result or "error" in result:
            return 0.0, {}

        scores = {}
        
        components = ["venue", "catering", "decor"]
        provided_components = sum(1 for comp in components if result.get(comp) and result[comp].get("options"))
        scores["completeness_score"] = (provided_components / len(components)) * 30

        total_price = result.get("total_price", {}).get("final_price", float('inf'))
        budget = criterios.get("presupuesto_total", 0)
        if budget and budget > 0 and total_price != float('inf'):
            if total_price <= budget:
                scores["budget_adherence_score"] = 20 * (1 - (budget - total_price) / budget)
            else:
                scores["budget_adherence_score"] = -20 # Penalización por exceder
        else:
            scores["budget_adherence_score"] = 0

        guest_count = criterios.get("guest_count", 0)
        venue_options = result.get("venue", {}).get("options", [{}])
        if guest_count > 0 and venue_options and "capacity" in venue_options[0]:
            venue_capacity = venue_options[0].get("capacity", 0)
            if venue_capacity >= guest_count:
                scores["capacity_adherence_score"] = 20
            else:
                scores["capacity_adherence_score"] = -20
        else:
            scores["capacity_adherence_score"] = 0
            
        info_score = len(json.dumps(result)) / 1000
        scores["information_richness_score"] = min(info_score, 30)

        total_score = sum(scores.values())
        return round(max(0, total_score), 2), scores

    def _analyze_results(self) -> List[ExperimentResult]:
        """Analiza los datos recopilados y genera resultados estadísticos."""
        if not self.results_data:
            return []

        df = pd.DataFrame(self.results_data)
        
        analysis_overall = self._perform_t_test(df['quality_score_rag'], df['quality_score_no_rag'], "Overall Improvement")

        analysis_by_difficulty = []
        for difficulty, group in df.groupby('difficulty'):
            if len(group) < 2: continue
            analysis = self._perform_t_test(group['quality_score_rag'], group['quality_score_no_rag'], f"Improvement for {difficulty} difficulty")
            analysis_by_difficulty.append(analysis)
            
        return [analysis_overall] + analysis_by_difficulty

    def _perform_t_test(self, sample1: pd.Series, sample2: pd.Series, name: str) -> ExperimentResult:
        """Realiza una prueba t pareada."""
        sample1_clean = sample1.dropna()
        sample2_clean = sample2.dropna()
        
        if len(sample1_clean) < 2 or len(sample2_clean) < 2 or len(sample1_clean) != len(sample2_clean):
             return ExperimentResult(experiment_name=name, timestamp=pd.Timestamp.now().isoformat(), sample_size=0, test_statistic=0, p_value=1, effect_size=0, confidence_interval=(0,0), power_achieved=0, conclusion="Not enough data", assumptions_met=False, effect_significance='none', recommendations=[])

        t_stat, p_value = stats.ttest_rel(sample1_clean, sample2_clean)
        
        diff = np.array(sample1_clean) - np.array(sample2_clean)
        mean_diff = np.mean(diff)
        
        if np.std(diff, ddof=1) == 0:
            cohens_d = 0.0
        else:
            cohens_d = mean_diff / np.std(diff, ddof=1)
        
        try:
            sem = stats.sem(diff)
            if sem > 0:
                ci = stats.t.interval(0.95, len(diff)-1, loc=mean_diff, scale=sem)
            else:
                ci = (mean_diff, mean_diff)
        except:
            ci = (0,0)

        return ExperimentResult(
            experiment_name=name,
            timestamp=pd.Timestamp.now().isoformat(),
            sample_size=len(sample1_clean),
            test_statistic=t_stat,
            p_value=p_value,
            effect_size=cohens_d,
            confidence_interval=ci,
            power_achieved=0,
            conclusion=f"RAG {'significantly improves' if p_value < 0.05 else 'does not significantly improve'} quality (p={p_value:.3f}).",
            assumptions_met=True,
            effect_significance=self.effect_size_calculator.interpret_effect_size(cohens_d),
            recommendations=[]
        )
    
    def generate_visualizations(self, save_path: str = None):
        if not self.results_data:
            return
        
        df = pd.DataFrame(self.results_data)
        if df.empty:
            return

        if not self.output_dir:
            print("No output directory specified for visualizations.")
            return
        
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # 1. Boxplot de Puntuaciones de Calidad (RAG vs No-RAG)
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=df[['quality_score_no_rag', 'quality_score_rag']])
        plt.title('Comparación de Puntuación de Calidad: RAG vs. No-RAG')
        plt.ylabel('Puntuación de Calidad')
        plt.savefig(f"{self.output_dir}/quality_scores_boxplot.png")
        plt.close()

        # 2. Distribución de la Mejora
        plt.figure(figsize=(10, 6))
        sns.histplot(df['improvement'], kde=True, bins=15)
        plt.title('Distribución de la Mejora en la Puntuación de Calidad (RAG - No-RAG)')
        plt.xlabel('Mejora')
        plt.savefig(f"{self.output_dir}/improvement_distribution.png")
        plt.close()

        # 3. Mejora por Nivel de Dificultad
        plt.figure(figsize=(12, 7))
        sns.boxplot(x='difficulty', y='improvement', data=df, order=['low', 'medium', 'high'])
        plt.title('Mejora de Calidad por Dificultad de la Consulta')
        plt.xlabel('Dificultad')
        plt.ylabel('Mejora (RAG - No-RAG)')
        plt.savefig(f"{self.output_dir}/improvement_by_difficulty.png")
        plt.close()

        print(f"Visualizaciones guardadas en {self.output_dir}")

def run_golden_set_experiment(system_components: Dict[str, Any]) -> List[ExperimentResult]:
    """Función de ayuda para ejecutar el experimento de validación del Golden Set."""
    config = ExperimentConfig(
        name="Golden Set Validation",
        description="Evalúa el rendimiento contra un conjunto de datos de prueba predefinido.",
    )
    
    experiment = GoldenSetValidationExperiment(
        config=config,
        system_components=system_components,
        output_dir="results/golden_set_validation"
    )
    
    return experiment.run() 