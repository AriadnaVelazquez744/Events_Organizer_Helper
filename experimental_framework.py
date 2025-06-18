#!/usr/bin/env python3
"""
Framework de Experimentación Estadística para el Sistema de Planificación de Eventos
Implementa experimentos robustos con validación estadística completa.
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# Importaciones estadísticas
from scipy import stats
from scipy.stats import ttest_rel, ttest_ind, f_oneway, chi2_contingency
from scipy.stats import pearsonr, spearmanr, kendalltau
from scipy.stats import shapiro, normaltest, anderson
from scipy.stats import mannwhitneyu, kruskal, wilcoxon
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score, KFold
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.power import TTestPower
from statsmodels.stats.multicomp import pairwise_tukeyhsd

@dataclass
class ExperimentConfig:
    """Configuración base para experimentos."""
    name: str
    description: str
    alpha: float = 0.05  # Nivel de significancia
    power: float = 0.8   # Potencia deseada
    effect_size: float = 0.5  # Tamaño del efecto
    min_sample_size: int = 30
    max_sample_size: int = 1000
    random_seed: int = 42

@dataclass
class ExperimentResult:
    """Resultado de un experimento estadístico."""
    experiment_name: str
    timestamp: str
    sample_size: int
    test_statistic: float
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    power_achieved: float
    conclusion: str
    assumptions_met: bool
    effect_significance: str  # 'small', 'medium', 'large'
    recommendations: List[str]

class StatisticalValidator:
    """Validador de supuestos estadísticos."""
    
    @staticmethod
    def check_normality(data: np.ndarray, alpha: float = 0.05) -> Dict[str, Any]:
        """Verifica normalidad usando múltiples tests."""
        results = {}
        
        # Test de Shapiro-Wilk
        shapiro_stat, shapiro_p = shapiro(data)
        results['shapiro'] = {
            'statistic': shapiro_stat,
            'p_value': shapiro_p,
            'is_normal': shapiro_p > alpha
        }
        
        # Test de D'Agostino
        dagostino_stat, dagostino_p = normaltest(data)
        results['dagostino'] = {
            'statistic': dagostino_stat,
            'p_value': dagostino_p,
            'is_normal': dagostino_p > alpha
        }
        
        # Test de Anderson-Darling
        anderson_result = anderson(data)
        results['anderson'] = {
            'statistic': anderson_result.statistic,
            'critical_values': anderson_result.critical_values,
            'significance_levels': anderson_result.significance_level,
            'is_normal': anderson_result.statistic < anderson_result.critical_values[2]
        }
        
        # Conclusión general
        results['overall_normal'] = (
            results['shapiro']['is_normal'] and 
            results['dagostino']['is_normal'] and 
            results['anderson']['is_normal']
        )
        
        return results
    
    @staticmethod
    def check_homogeneity_of_variance(groups: List[np.ndarray], alpha: float = 0.05) -> Dict[str, Any]:
        """Verifica homogeneidad de varianzas usando Levene's test."""
        levene_stat, levene_p = stats.levene(*groups)
        return {
            'statistic': levene_stat,
            'p_value': levene_p,
            'homogeneous': levene_p > alpha
        }
    
    @staticmethod
    def check_independence(data: np.ndarray, method: str = 'durbin_watson') -> Dict[str, Any]:
        """Verifica independencia de observaciones."""
        if method == 'durbin_watson':
            # Para datos de series temporales
            if len(data) > 1:
                dw_stat = sm.stats.durbin_watson(data)
                return {
                    'statistic': dw_stat,
                    'independent': 1.5 < dw_stat < 2.5,
                    'method': 'durbin_watson'
                }
        return {'independent': True, 'method': 'assumed'}

class EffectSizeCalculator:
    """Calculadora de tamaños de efecto."""
    
    @staticmethod
    def cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
        """Calcula el tamaño de efecto de Cohen's d."""
        n1, n2 = len(group1), len(group2)
        pooled_std = np.sqrt(((n1-1)*np.var(group1, ddof=1) + (n2-1)*np.var(group2, ddof=1)) / (n1+n2-2))
        return (np.mean(group1) - np.mean(group2)) / pooled_std
    
    @staticmethod
    def eta_squared(ss_between: float, ss_total: float) -> float:
        """Calcula eta-squared para ANOVA."""
        return ss_between / ss_total
    
    @staticmethod
    def interpret_effect_size(effect_size: float, test_type: str = 'cohens_d') -> str:
        """Interpreta el tamaño del efecto."""
        if test_type == 'cohens_d':
            if abs(effect_size) < 0.2:
                return 'small'
            elif abs(effect_size) < 0.5:
                return 'medium'
            else:
                return 'large'
        elif test_type == 'eta_squared':
            if effect_size < 0.01:
                return 'small'
            elif effect_size < 0.06:
                return 'medium'
            else:
                return 'large'
        return 'unknown'

class PowerAnalyzer:
    """Analizador de potencia estadística."""
    
    @staticmethod
    def calculate_sample_size(effect_size: float, alpha: float = 0.05, power: float = 0.8) -> int:
        """Calcula el tamaño de muestra necesario."""
        power_analysis = TTestPower()
        sample_size = power_analysis.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            power=power,
            alternative='two-sided'
        )
        return int(np.ceil(sample_size))
    
    @staticmethod
    def calculate_power(sample_size: int, effect_size: float, alpha: float = 0.05) -> float:
        """Calcula la potencia alcanzada."""
        power_analysis = TTestPower()
        power = power_analysis.solve_power(
            effect_size=effect_size,
            alpha=alpha,
            nobs=sample_size,
            alternative='two-sided'
        )
        return power

class DataCollector:
    """Recolector de datos para experimentos."""
    
    def __init__(self, system_components: Dict[str, Any]):
        self.components = system_components
        self.data_buffer = []
    
    def collect_bdi_metrics(self, session_id: str, task_type: str) -> Dict[str, Any]:
        """Recolecta métricas del sistema BDI."""
        try:
            planner = self.components.get('planner')
            memory = self.components.get('memory')
            
            if not planner or not memory:
                return {}
            
            # Obtener información de la sesión
            session_info = memory.get_session_info(session_id)
            beliefs = memory.get_beliefs(session_id)
            
            # Métricas BDI
            metrics = {
                'session_id': session_id,
                'task_type': task_type,
                'timestamp': datetime.now().isoformat(),
                'beliefs_count': len(beliefs.get_all()) if beliefs else 0,
                'desires_count': len(planner.desires.get(session_id, [])),
                'intentions_count': len(planner.intentions.get(session_id, [])),
                'pending_tasks': len(planner.task_queue.get(session_id, [])),
                'completed_tasks': len([t for t in planner.task_queue.get(session_id, []) 
                                      if t.status == 'completed']),
                'failed_tasks': len([t for t in planner.task_queue.get(session_id, []) 
                                   if t.status == 'error']),
                'retry_count': sum(t.retry_count for t in planner.task_queue.get(session_id, [])),
                'session_duration': self._calculate_session_duration(session_info),
                'complexity_score': self._calculate_complexity_score(session_info)
            }
            
            return metrics
        except Exception as e:
            print(f"[DataCollector] Error collecting BDI metrics: {str(e)}")
            return {}
    
    def collect_rag_metrics(self, rag_type: str, query: Dict, results: List[Dict]) -> Dict[str, Any]:
        """Recolecta métricas de sistemas RAG."""
        try:
            metrics = {
                'rag_type': rag_type,
                'timestamp': datetime.now().isoformat(),
                'query_complexity': len(query),
                'results_count': len(results),
                'avg_result_confidence': np.mean([r.get('confidence', 0) for r in results]),
                'max_result_confidence': max([r.get('confidence', 0) for r in results]),
                'min_result_confidence': min([r.get('confidence', 0) for r in results]),
                'result_variance': np.var([r.get('confidence', 0) for r in results]),
                'response_time': query.get('response_time', 0),
                'pattern_match_score': self._calculate_pattern_match(query, results)
            }
            
            return metrics
        except Exception as e:
            print(f"[DataCollector] Error collecting RAG metrics: {str(e)}")
            return {}
    
    def collect_performance_metrics(self, operation: str, start_time: datetime, 
                                  end_time: datetime, resource_usage: Dict) -> Dict[str, Any]:
        """Recolecta métricas de rendimiento."""
        duration = (end_time - start_time).total_seconds()
        
        return {
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'memory_usage_mb': resource_usage.get('memory_mb', 0),
            'cpu_usage_percent': resource_usage.get('cpu_percent', 0),
            'disk_io_mb': resource_usage.get('disk_io_mb', 0),
            'network_requests': resource_usage.get('network_requests', 0),
            'throughput_ops_per_sec': 1.0 / duration if duration > 0 else 0
        }
    
    def collect_message_bus_metrics(self, message: Dict, response: Dict, 
                                  processing_time: float) -> Dict[str, Any]:
        """Recolecta métricas del MessageBus."""
        return {
            'timestamp': datetime.now().isoformat(),
            'message_type': message.get('tipo', ''),
            'source_agent': message.get('origen', ''),
            'target_agent': message.get('destino', ''),
            'message_size_bytes': len(json.dumps(message)),
            'processing_time_seconds': processing_time,
            'response_size_bytes': len(json.dumps(response)) if response else 0,
            'success': response is not None,
            'queue_depth': len(self.components.get('bus', {}).message_queue.queue) if 'bus' in self.components else 0
        }
    
    def _calculate_session_duration(self, session_info: Dict) -> float:
        """Calcula la duración de una sesión."""
        if not session_info:
            return 0.0
        
        created_at = session_info.get('created_at')
        if not created_at:
            return 0.0
        
        try:
            created_time = datetime.fromisoformat(created_at)
            return (datetime.now() - created_time).total_seconds()
        except:
            return 0.0
    
    def _calculate_complexity_score(self, session_info: Dict) -> float:
        """Calcula un score de complejidad de la sesión."""
        if not session_info:
            return 0.0
        
        # Factores de complejidad
        factors = {
            'guest_count': session_info.get('guest_count', 0) / 100.0,  # Normalizado
            'budget': session_info.get('budget', 0) / 100000.0,  # Normalizado
            'style_complexity': len(session_info.get('style', '')) / 20.0,
            'requirements_count': len(session_info.get('requirements', [])) / 10.0
        }
        
        return sum(factors.values()) / len(factors)

class ExperimentReporter:
    """Generador de reportes de experimentos."""
    
    def __init__(self, output_dir: str = "experiment_results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def generate_report(self, experiment_name: str, results: List[ExperimentResult], 
                       data_summary: Dict[str, Any]) -> str:
        """Genera un reporte completo del experimento."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"{self.output_dir}/{experiment_name}_{timestamp}_report.html"
        
        # Crear reporte HTML
        html_content = self._create_html_report(experiment_name, results, data_summary)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return report_file
    
    def _create_html_report(self, experiment_name: str, results: List[ExperimentResult], 
                           data_summary: Dict[str, Any]) -> str:
        """Crea el contenido HTML del reporte."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reporte de Experimento: {experiment_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #007acc; }}
                .result {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 3px; }}
                .significant {{ background-color: #d4edda; border-left-color: #28a745; }}
                .not-significant {{ background-color: #f8d7da; border-left-color: #dc3545; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Reporte de Experimento: {experiment_name}</h1>
                <p>Generado el: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            </div>
            
            <div class="section">
                <h2>Resumen de Datos</h2>
                <table>
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Total de muestras</td><td>{data_summary.get('total_samples', 0)}</td></tr>
                    <tr><td>Duración del experimento</td><td>{data_summary.get('duration', 'N/A')}</td></tr>
                    <tr><td>Experimentos realizados</td><td>{len(results)}</td></tr>
                </table>
            </div>
            
            <div class="section">
                <h2>Resultados de Experimentos</h2>
        """
        
        for i, result in enumerate(results):
            significance_class = "significant" if result.p_value < 0.05 else "not-significant"
            html += f"""
                <div class="result {significance_class}">
                    <h3>Experimento {i+1}: {result.experiment_name}</h3>
                    <p><strong>Conclusión:</strong> {result.conclusion}</p>
                    <p><strong>Estadístico de prueba:</strong> {result.test_statistic:.4f}</p>
                    <p><strong>P-valor:</strong> {result.p_value:.4f}</p>
                    <p><strong>Tamaño del efecto:</strong> {result.effect_size:.4f} ({result.effect_significance})</p>
                    <p><strong>Potencia alcanzada:</strong> {result.power_achieved:.4f}</p>
                    <p><strong>Supuestos cumplidos:</strong> {'Sí' if result.assumptions_met else 'No'}</p>
                    <ul>
                        <li><strong>Recomendaciones:</strong></li>
                        {''.join([f'<li>{rec}</li>' for rec in result.recommendations])}
                    </ul>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html

class BaseExperiment:
    """Clase base para todos los experimentos."""
    
    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any]):
        self.config = config
        self.components = system_components
        self.data_collector = DataCollector(system_components)
        self.validator = StatisticalValidator()
        self.effect_calculator = EffectSizeCalculator()
        self.power_analyzer = PowerAnalyzer()
        self.reporter = ExperimentReporter()
        
        # Configurar semilla aleatoria
        np.random.seed(config.random_seed)
        
        # Buffer de datos
        self.data_buffer = []
        self.results = []
    
    def run(self) -> List[ExperimentResult]:
        """Ejecuta el experimento completo."""
        raise NotImplementedError("Subclases deben implementar este método")
    
    def validate_assumptions(self, data: np.ndarray) -> bool:
        """Valida los supuestos estadísticos básicos."""
        normality_result = self.validator.check_normality(data, self.config.alpha)
        return normality_result['overall_normal']
    
    def calculate_confidence_interval(self, data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
        """Calcula el intervalo de confianza."""
        mean = np.mean(data)
        std_err = stats.sem(data)
        ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=std_err)
        return ci
    
    def _serialize_data_for_json(self, data):
        """Serializa datos para JSON, manejando tipos especiales."""
        if isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        elif isinstance(data, np.ndarray):
            # Convertir NaN a None para JSON
            return np.where(np.isnan(data), None, data).tolist()
        elif isinstance(data, (datetime, pd.Timestamp)):
            return data.isoformat()
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            # Manejar NaN en floats
            if np.isnan(data) or np.isinf(data):
                return None
            return float(data)
        elif isinstance(data, dict):
            return {k: self._serialize_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data_for_json(item) for item in data]
        else:
            return data

    def save_data(self, filename: str = None):
        """Guarda los datos del experimento."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.config.name}_{timestamp}_data.json"
        
        data_to_save = {
            'experiment_config': self.config.__dict__,
            'data_buffer': self.data_buffer,
            'results': [result.__dict__ for result in self.results],
            'timestamp': datetime.now().isoformat()
        }
        
        # Serializar datos para JSON
        serialized_data = self._serialize_data_for_json(data_to_save)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)
        
        print(f"[BaseExperiment] Datos guardados en: {filename}")
    
    def generate_visualizations(self, save_path: str = None):
        """Genera visualizaciones de los resultados."""
        if not self.data_buffer:
            print("[BaseExperiment] No hay datos para visualizar")
            return
        
        if not save_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            save_path = f"{self.config.name}_{timestamp}_plots.png"
        
        # Crear figura con múltiples subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Resultados del Experimento: {self.config.name}', fontsize=16)
        
        # Convertir datos a DataFrame
        df = pd.DataFrame(self.data_buffer)
        
        # Plot 1: Distribución de métricas principales
        if len(df.columns) > 0:
            numeric_cols = df.select_dtypes(include=[np.number]).columns[:3]
            for i, col in enumerate(numeric_cols):
                if i < 3:
                    axes[0, 0].hist(df[col].dropna(), alpha=0.7, label=col)
            axes[0, 0].set_title('Distribución de Métricas')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Correlaciones
        if len(df.select_dtypes(include=[np.number]).columns) > 1:
            corr_matrix = df.select_dtypes(include=[np.number]).corr()
            sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, ax=axes[0, 1])
            axes[0, 1].set_title('Matriz de Correlaciones')
        
        # Plot 3: Series temporales (si hay timestamp)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            if len(df.columns) > 1:
                numeric_col = df.select_dtypes(include=[np.number]).columns[0]
                axes[1, 0].plot(df['timestamp'], df[numeric_col])
                axes[1, 0].set_title(f'{numeric_col} vs Tiempo')
                axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Plot 4: Box plots por categorías
        if len(df.columns) > 1:
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0 and len(df.select_dtypes(include=[np.number]).columns) > 0:
                cat_col = categorical_cols[0]
                num_col = df.select_dtypes(include=[np.number]).columns[0]
                df.boxplot(column=num_col, by=cat_col, ax=axes[1, 1])
                axes[1, 1].set_title(f'{num_col} por {cat_col}')
        
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"[BaseExperiment] Visualizaciones guardadas en: {save_path}")

# Configuración global para experimentos
EXPERIMENT_CONFIGS = {
    'bdi_effectiveness': ExperimentConfig(
        name="BDI_Effectiveness",
        description="Análisis de efectividad del ciclo BDI",
        alpha=0.05,
        power=0.8,
        effect_size=0.5
    ),
    'rag_precision': ExperimentConfig(
        name="RAG_Precision",
        description="Análisis de precisión de sistemas RAG",
        alpha=0.05,
        power=0.8,
        effect_size=0.3
    ),
    'system_performance': ExperimentConfig(
        name="System_Performance",
        description="Análisis de rendimiento del sistema",
        alpha=0.05,
        power=0.8,
        effect_size=0.4
    ),
    'integration_effectiveness': ExperimentConfig(
        name="Integration_Effectiveness",
        description="Análisis de efectividad de integración",
        alpha=0.05,
        power=0.8,
        effect_size=0.4
    )
} 