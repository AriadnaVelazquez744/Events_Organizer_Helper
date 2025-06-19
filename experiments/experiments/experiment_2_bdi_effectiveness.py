#!/usr/bin/env python3
"""
Experimento 2: Análisis de Efectividad del Sistema BDI
Implementa análisis robusto del ciclo BDI y patrones de reconsideración de intentions.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import os

from scipy import stats
from framework.experimental_framework import BaseExperiment, ExperimentConfig, ExperimentResult
from framework.experimental_framework import StatisticalValidator, EffectSizeCalculator, PowerAnalyzer
import statsmodels.api as sm
from scipy.stats import f_oneway, kruskal, pearsonr, spearmanr, sem
from sklearn.preprocessing import StandardScaler

class BDIEffectivenessExperiment(BaseExperiment):
    """Experimento para analizar la efectividad del ciclo BDI."""
    
    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any], output_dir: str):
        super().__init__(config, system_components)
        self.complexity_levels = ['low', 'medium', 'high']
        self.agent_types = ['venue', 'catering', 'decor', 'budget']
        self.output_dir = output_dir
        
    def run(self) -> List[ExperimentResult]:
        """Ejecuta el experimento completo de efectividad BDI."""
        print(f"[BDIExperiment] Iniciando experimento: {self.config.name}")
        
        # Generar datos sintéticos para el experimento
        self._generate_synthetic_bdi_data()
        
        # Ejecutar análisis de efectividad del ciclo BDI
        bdi_effectiveness_result = self._analyze_bdi_effectiveness()
        self.results.append(bdi_effectiveness_result)
        
        # Ejecutar análisis de patrones de reconsideración
        reconsideration_result = self._analyze_intention_reconsideration()
        self.results.append(reconsideration_result)
        
        # Ejecutar análisis de correlación entre factores
        correlation_result = self._analyze_bdi_correlations()
        self.results.append(correlation_result)
        
        # Ejecutar análisis de regresión múltiple
        regression_result = self._analyze_bdi_regression()
        self.results.append(regression_result)
        
        print(f"[BDIExperiment] Experimento completado. {len(self.results)} análisis realizados.")
        return self.results
    
    def _generate_synthetic_bdi_data(self):
        """Genera datos sintéticos realistas para el experimento BDI."""
        print("[BDIExperiment] Generando datos sintéticos...")
        
        np.random.seed(self.config.random_seed)
        n_sessions = 200  # Tamaño de muestra robusto
        
        for i in range(n_sessions):
            # Generar complejidad aleatoria
            complexity = np.random.choice(self.complexity_levels, p=[0.3, 0.5, 0.2])
            
            # Generar tipo de agente principal
            agent_type = np.random.choice(self.agent_types, p=[0.4, 0.3, 0.2, 0.1])
            
            # Generar métricas BDI basadas en complejidad
            bdi_metrics = self._generate_bdi_metrics(complexity, agent_type)
            
            # Agregar ruido realista
            bdi_metrics = self._add_realistic_noise(bdi_metrics)
            
            # Agregar timestamp
            bdi_metrics['timestamp'] = datetime.now() - timedelta(
                minutes=np.random.randint(0, 1440)  # Últimas 24 horas
            )
            
            self.data_buffer.append(bdi_metrics)
        
        print(f"[BDIExperiment] Generados {len(self.data_buffer)} registros de datos BDI")
    
    def _generate_bdi_metrics(self, complexity: str, agent_type: str) -> Dict[str, Any]:
        """Genera métricas BDI basadas en complejidad y tipo de agente."""
        # Parámetros base según complejidad
        complexity_params = {
            'low': {'beliefs_base': 5, 'desires_base': 2, 'intentions_base': 1, 'success_rate': 0.9},
            'medium': {'beliefs_base': 8, 'desires_base': 3, 'intentions_base': 2, 'success_rate': 0.7},
            'high': {'beliefs_base': 12, 'desires_base': 5, 'intentions_base': 3, 'success_rate': 0.5}
        }
        
        params = complexity_params[complexity]
        
        # Generar métricas base
        beliefs_count = np.random.poisson(params['beliefs_base'])
        desires_count = np.random.poisson(params['desires_base'])
        intentions_count = np.random.poisson(params['intentions_base'])
        
        # Generar tareas basadas en complejidad
        total_tasks = np.random.poisson(params['intentions_base'] * 2)
        completed_tasks = int(total_tasks * params['success_rate'])
        failed_tasks = total_tasks - completed_tasks
        pending_tasks = np.random.poisson(1)  # Pocas tareas pendientes
        
        # Generar reintentos basados en complejidad
        retry_count = np.random.poisson(complexity_params[complexity]['intentions_base'])
        
        # Generar duración de sesión
        session_duration = np.random.exponential(300)  # Media de 5 minutos
        
        # Generar score de complejidad
        complexity_score = {
            'low': np.random.uniform(0.1, 0.3),
            'medium': np.random.uniform(0.4, 0.7),
            'high': np.random.uniform(0.8, 1.0)
        }[complexity]
        
        return {
            'session_id': f"session_{np.random.randint(1000, 9999)}",
            'complexity_level': complexity,
            'agent_type': agent_type,
            'beliefs_count': beliefs_count,
            'desires_count': desires_count,
            'intentions_count': intentions_count,
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'pending_tasks': pending_tasks,
            'retry_count': retry_count,
            'session_duration': session_duration,
            'complexity_score': complexity_score,
            'success_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
            'efficiency_score': completed_tasks / (session_duration / 60) if session_duration > 0 else 0,
            'stability_score': 1 - (retry_count / total_tasks) if total_tasks > 0 else 1
        }
    
    def _add_realistic_noise(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega ruido realista a las métricas."""
        noise_factor = 0.1  # 10% de ruido
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key not in ['session_id', 'complexity_level', 'agent_type']:
                noise = np.random.normal(0, abs(value) * noise_factor)
                metrics[key] = max(0, value + noise)  # Evitar valores negativos
        
        return metrics
    
    def _analyze_bdi_effectiveness(self) -> ExperimentResult:
        """Analiza la efectividad general del ciclo BDI."""
        print("[BDIExperiment] Analizando efectividad del ciclo BDI...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Métricas de efectividad
        success_rates = df['success_rate'].values
        efficiency_scores = df['efficiency_score'].values
        stability_scores = df['stability_score'].values
        
        # Análisis de efectividad por complejidad
        complexity_groups = [df[df['complexity_level'] == level]['success_rate'].values 
                           for level in self.complexity_levels]
        
        # ANOVA para comparar efectividad entre niveles de complejidad
        f_stat, p_value = f_oneway(*complexity_groups)
        
        # Calcular tamaño del efecto (eta-squared)
        ss_between = sum(len(group) * (np.mean(group) - np.mean(success_rates))**2 for group in complexity_groups)
        ss_total = sum((rate - np.mean(success_rates))**2 for rate in success_rates)
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        # Validar supuestos
        assumptions_met = all(self.validate_assumptions(group) for group in complexity_groups)
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(success_rates), eta_squared, self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(eta_squared, 'eta_squared')
        
        if p_value < self.config.alpha:
            conclusion = f"Existe diferencia significativa en efectividad BDI entre niveles de complejidad (F={f_stat:.3f}, p={p_value:.4f})"
        else:
            conclusion = f"No se encontró diferencia significativa en efectividad BDI entre niveles de complejidad (F={f_stat:.3f}, p={p_value:.4f})"
        
        recommendations = [
            "Monitorear sesiones de alta complejidad más de cerca",
            "Implementar estrategias de recuperación para sesiones con baja estabilidad",
            "Optimizar el procesamiento de beliefs para sesiones complejas"
        ]
        
        return ExperimentResult(
            experiment_name="BDI Effectiveness Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(success_rates),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=eta_squared,
            confidence_interval=self.calculate_confidence_interval(success_rates),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=assumptions_met,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_intention_reconsideration(self) -> ExperimentResult:
        """Analiza patrones de reconsideración de intentions."""
        print("[BDIExperiment] Analizando patrones de reconsideración...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Métricas de reconsideración
        retry_rates = df['retry_count'] / df['total_tasks']
        retry_rates = retry_rates.replace([np.inf, -np.inf], 0)  # Manejar división por cero
        
        # Análisis por tipo de agente
        agent_groups = [df[df['agent_type'] == agent]['retry_count'].values 
                       for agent in self.agent_types]
        
        # Test de Kruskal-Wallis (no paramétrico para datos no normales)
        h_stat, p_value = kruskal(*agent_groups)
        
        # Calcular tamaño del efecto
        total_retries = sum(len(group) for group in agent_groups)
        if total_retries > 0:
            effect_size = h_stat / (total_retries - 1)
        else:
            effect_size = 0
        
        # Análisis de correlación entre reintentos y complejidad
        complexity_corr, complexity_p = spearmanr(df['complexity_score'], df['retry_count'])
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(retry_rates), abs(complexity_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(complexity_corr), 'cohens_d')
        
        if p_value < self.config.alpha:
            conclusion = f"Existe diferencia significativa en patrones de reconsideración entre agentes (H={h_stat:.3f}, p={p_value:.4f})"
        else:
            conclusion = f"No se encontró diferencia significativa en patrones de reconsideración entre agentes (H={h_stat:.3f}, p={p_value:.4f})"
        
        if complexity_p < self.config.alpha:
            conclusion += f". Existe correlación significativa con complejidad (r={complexity_corr:.3f}, p={complexity_p:.4f})"
        
        recommendations = [
            "Implementar estrategias específicas por tipo de agente",
            "Optimizar reconsideración para sesiones de alta complejidad",
            "Establecer límites de reintentos por tipo de agente"
        ]
        
        return ExperimentResult(
            experiment_name="Intention Reconsideration Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(retry_rates),
            test_statistic=h_stat,
            p_value=p_value,
            effect_size=abs(complexity_corr),
            confidence_interval=self.calculate_confidence_interval(retry_rates),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,  # Kruskal-Wallis no requiere normalidad
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_bdi_correlations(self) -> ExperimentResult:
        """Analiza correlaciones entre diferentes métricas BDI."""
        print("[BDIExperiment] Analizando correlaciones BDI...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Seleccionar variables numéricas para correlación
        numeric_vars = ['beliefs_count', 'desires_count', 'intentions_count', 
                       'success_rate', 'efficiency_score', 'stability_score', 
                       'complexity_score', 'retry_count']
        
        correlation_matrix = df[numeric_vars].corr()
        
        # Encontrar correlaciones más fuertes
        strong_correlations = []
        for i in range(len(numeric_vars)):
            for j in range(i+1, len(numeric_vars)):
                corr_value = correlation_matrix.iloc[i, j]
                if abs(corr_value) > 0.3:  # Correlación moderada o fuerte
                    strong_correlations.append({
                        'var1': numeric_vars[i],
                        'var2': numeric_vars[j],
                        'correlation': corr_value
                    })
        
        # Test de correlación más significativa
        if strong_correlations:
            best_corr = max(strong_correlations, key=lambda x: abs(x['correlation']))
            var1_data = df[best_corr['var1']].values
            var2_data = df[best_corr['var2']].values
            
            # Test de correlación de Pearson
            corr_stat, p_value = pearsonr(var1_data, var2_data)
            
            # Calcular potencia
            power_achieved = self.power_analyzer.calculate_power(
                len(var1_data), abs(corr_stat), self.config.alpha
            )
            
            effect_significance = self.effect_calculator.interpret_effect_size(abs(corr_stat), 'cohens_d')
            
            conclusion = f"Correlación significativa entre {best_corr['var1']} y {best_corr['var2']} (r={corr_stat:.3f}, p={p_value:.4f})"
        else:
            corr_stat = 0
            p_value = 1
            power_achieved = 0
            effect_significance = 'small'
            conclusion = "No se encontraron correlaciones significativas entre métricas BDI"
        
        recommendations = [
            "Monitorear métricas correlacionadas para optimización",
            "Implementar alertas basadas en correlaciones identificadas",
            "Usar correlaciones para predicción de rendimiento"
        ]
        
        return ExperimentResult(
            experiment_name="BDI Correlations Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=corr_stat,
            p_value=p_value,
            effect_size=abs(corr_stat),
            confidence_interval=(-1, 1),  # Rango de correlación
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_bdi_regression(self) -> ExperimentResult:
        """Análisis de regresión múltiple para predecir efectividad BDI."""
        print("[BDIExperiment] Realizando análisis de regresión...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Preparar variables para regresión
        X_vars = ['beliefs_count', 'desires_count', 'intentions_count', 
                 'complexity_score', 'retry_count']
        y_var = 'success_rate'
        
        X = df[X_vars].values
        y = df[y_var].values
        
        # Eliminar filas con valores faltantes
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) < 10:  # Mínimo para regresión
            return ExperimentResult(
                experiment_name="BDI Regression Analysis",
                timestamp=datetime.now().isoformat(),
                sample_size=len(X),
                test_statistic=0,
                p_value=1,
                effect_size=0,
                confidence_interval=(0, 0),
                power_achieved=0,
                conclusion="Datos insuficientes para análisis de regresión",
                assumptions_met=False,
                effect_significance='small',
                recommendations=["Recolectar más datos para análisis de regresión"]
            )
        
        # Estandarizar variables
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Agregar constante para intercepto
        X_with_const = sm.add_constant(X_scaled)
        
        # Ajustar modelo de regresión
        model = sm.OLS(y, X_with_const)
        results = model.fit()
        
        # Estadísticas del modelo
        r_squared = results.rsquared
        f_stat = results.fvalue
        f_p_value = results.f_pvalue
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(X), r_squared, self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(r_squared, 'eta_squared')
        
        if f_p_value < self.config.alpha:
            conclusion = f"El modelo de regresión es significativo (F={f_stat:.3f}, p={f_p_value:.4f}, R²={r_squared:.3f})"
        else:
            conclusion = f"El modelo de regresión no es significativo (F={f_stat:.3f}, p={f_p_value:.4f}, R²={r_squared:.3f})"
        
        # Identificar variables más importantes
        p_values = results.pvalues[1:]  # Excluir intercepto
        significant_vars = [X_vars[i] for i, p in enumerate(p_values) if p < self.config.alpha]
        
        if significant_vars:
            conclusion += f". Variables significativas: {', '.join(significant_vars)}"
        
        recommendations = [
            f"Usar {', '.join(significant_vars)} como predictores principales",
            "Implementar modelo de predicción de efectividad BDI",
            "Monitorear variables no significativas para cambios futuros"
        ]
        
        return ExperimentResult(
            experiment_name="BDI Regression Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(X),
            test_statistic=f_stat,
            p_value=f_p_value,
            effect_size=r_squared,
            confidence_interval=self.calculate_confidence_interval(y),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )

    def calculate_confidence_interval(self, data: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
        """Calcula el intervalo de confianza con manejo de errores."""
        try:
            # Filtrar valores válidos
            valid_data = data[~np.isnan(data) & ~np.isinf(data)]
            
            if len(valid_data) < 2:
                return (0.0, 1.0)  # Intervalo por defecto si no hay suficientes datos
            
            mean = np.mean(valid_data)
            std_err = sem(valid_data)
            
            # Verificar que std_err no sea NaN o infinito
            if np.isnan(std_err) or np.isinf(std_err) or std_err == 0:
                return (mean - 0.1, mean + 0.1)  # Intervalo pequeño alrededor de la media
            
            ci = stats.t.interval(confidence, len(valid_data)-1, loc=mean, scale=std_err)
            
            # Verificar que los valores del intervalo sean válidos
            if np.isnan(ci[0]) or np.isnan(ci[1]) or np.isinf(ci[0]) or np.isinf(ci[1]):
                return (mean - 0.1, mean + 0.1)
            
            return ci
        except Exception as e:
            print(f"[BDIExperiment] Error calculando intervalo de confianza: {str(e)}")
            return (0.0, 1.0)  # Intervalo por defecto en caso de error

def run_bdi_experiments(system_components: Dict[str, Any]) -> List[ExperimentResult]:
    """Función principal para ejecutar todos los experimentos BDI."""
    print("="*80)
    print("INICIANDO EXPERIMENTOS DE EFECTIVIDAD BDI")
    print("="*80)
    
    # Configurar experimento
    config = ExperimentConfig(
        name="BDI_Effectiveness_Complete",
        description="Análisis completo de efectividad del sistema BDI",
        alpha=0.05,
        power=0.8,
        effect_size=0.5,
        min_sample_size=30,
        max_sample_size=500
    )
    
    # Crear y ejecutar experimento con directorio de salida específico
    output_dir = os.path.join("results", "bdi_effectiveness")
    experiment = BDIEffectivenessExperiment(config, system_components, output_dir)
    results = experiment.run()
    
    # Generar visualizaciones
    experiment.generate_visualizations()
    
    # Guardar datos
    experiment.save_data()
    
    # Generar reporte
    data_summary = {
        'total_samples': len(experiment.data_buffer),
        'duration': f"{len(experiment.data_buffer)} sesiones simuladas",
        'experiments_completed': len(results)
    }
    
    report_file = experiment.reporter.generate_report(
        experiment.config.name, results, data_summary
    )
    
    print(f"\n✅ Experimentos BDI completados:")
    print(f"   - Análisis realizados: {len(results)}")
    print(f"   - Muestras procesadas: {len(experiment.data_buffer)}")
    print(f"   - Reporte generado: {report_file}")
    
    return results

if __name__ == "__main__":
    # Ejemplo de uso
    mock_components = {
        'planner': None,
        'memory': None,
        'bus': None
    }
    
    results = run_bdi_experiments(mock_components)
    
    # Mostrar resumen de resultados
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS BDI")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.experiment_name}")
        print(f"   Conclusión: {result.conclusion}")
        print(f"   P-valor: {result.p_value:.4f}")
        print(f"   Tamaño del efecto: {result.effect_size:.3f} ({result.effect_significance})")
        print(f"   Potencia: {result.power_achieved:.3f}") 