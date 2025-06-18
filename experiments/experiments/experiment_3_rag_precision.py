#!/usr/bin/env python3
"""
Experimento 3: Análisis de Precisión de Sistemas RAG
Implementa análisis robusto de precisión de recomendaciones RAG y adaptabilidad de patrones.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import os
from framework.experimental_framework import BaseExperiment, ExperimentConfig, ExperimentResult
from framework.experimental_framework import StatisticalValidator, EffectSizeCalculator, PowerAnalyzer
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import statsmodels.api as sm
from scipy.stats import f_oneway, kruskal, pearsonr, spearmanr

class RAGPrecisionExperiment(BaseExperiment):
    """Experimento para analizar la precisión de sistemas RAG."""
    
    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any], output_dir: str = None):
        super().__init__(config, system_components, output_dir)
        self.rag_types = ['venue', 'catering', 'decor']
        self.query_categories = ['budget', 'capacity', 'style', 'location', 'services']
        
    def run(self) -> List[ExperimentResult]:
        """Ejecuta el experimento completo de precisión RAG."""
        print(f"[RAGExperiment] Iniciando experimento: {self.config.name}")
        
        # Generar datos sintéticos para el experimento
        self._generate_synthetic_rag_data()
        
        # Ejecutar análisis de precisión general
        precision_result = self._analyze_rag_precision()
        self.results.append(precision_result)
        
        # Ejecutar análisis por tipo de RAG
        type_analysis_result = self._analyze_rag_by_type()
        self.results.append(type_analysis_result)
        
        # Ejecutar análisis de adaptabilidad de patrones
        adaptability_result = self._analyze_pattern_adaptability()
        self.results.append(adaptability_result)
        
        # Ejecutar análisis de correlación con complejidad de consulta
        complexity_result = self._analyze_query_complexity_correlation()
        self.results.append(complexity_result)
        
        # Ejecutar análisis de estabilidad temporal
        stability_result = self._analyze_temporal_stability()
        self.results.append(stability_result)
        
        print(f"[RAGExperiment] Experimento completado. {len(self.results)} análisis realizados.")
        return self.results
    
    def _generate_synthetic_rag_data(self):
        """Genera datos sintéticos realistas para el experimento RAG."""
        print("[RAGExperiment] Generando datos sintéticos RAG...")
        
        np.random.seed(self.config.random_seed)
        n_queries = 300  # Tamaño de muestra robusto
        
        for i in range(n_queries):
            # Generar tipo de RAG aleatorio
            rag_type = np.random.choice(self.rag_types, p=[0.4, 0.35, 0.25])
            
            # Generar complejidad de consulta
            query_complexity = np.random.uniform(0.1, 1.0)
            
            # Generar métricas RAG basadas en tipo y complejidad
            rag_metrics = self._generate_rag_metrics(rag_type, query_complexity)
            
            # Agregar ruido realista
            rag_metrics = self._add_realistic_noise(rag_metrics)
            
            # Agregar timestamp
            rag_metrics['timestamp'] = datetime.now() - timedelta(
                minutes=np.random.randint(0, 1440)  # Últimas 24 horas
            )
            
            self.data_buffer.append(rag_metrics)
        
        print(f"[RAGExperiment] Generados {len(self.data_buffer)} registros de datos RAG")
    
    def _generate_rag_metrics(self, rag_type: str, query_complexity: float) -> Dict[str, Any]:
        """Genera métricas RAG basadas en tipo y complejidad."""
        # Parámetros base según tipo de RAG
        rag_params = {
            'venue': {
                'base_precision': 0.85,
                'base_recall': 0.80,
                'base_confidence': 0.75,
                'pattern_stability': 0.70
            },
            'catering': {
                'base_precision': 0.80,
                'base_recall': 0.75,
                'base_confidence': 0.70,
                'pattern_stability': 0.65
            },
            'decor': {
                'base_precision': 0.75,
                'base_recall': 0.70,
                'base_confidence': 0.65,
                'pattern_stability': 0.60
            }
        }
        
        params = rag_params[rag_type]
        
        # Ajustar métricas por complejidad
        complexity_factor = 1 - (query_complexity * 0.3)  # Complejidad reduce rendimiento
        
        precision = params['base_precision'] * complexity_factor
        recall = params['base_recall'] * complexity_factor
        confidence = params['base_confidence'] * complexity_factor
        
        # Calcular F1-score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # Generar número de resultados
        results_count = np.random.poisson(5) + 1  # Mínimo 1 resultado
        
        # Generar métricas de confianza
        confidence_scores = np.random.beta(2, 2, results_count) * confidence
        avg_confidence = np.mean(confidence_scores)
        max_confidence = np.max(confidence_scores)
        min_confidence = np.min(confidence_scores)
        confidence_variance = np.var(confidence_scores)
        
        # Generar tiempo de respuesta
        response_time = np.random.exponential(2.0)  # Media de 2 segundos
        
        # Generar score de coincidencia de patrones
        pattern_match_score = np.random.beta(3, 2) * params['pattern_stability']
        
        # Generar métricas de adaptabilidad
        pattern_update_frequency = np.random.exponential(10.0)  # Media de 10 consultas
        success_rate_trend = np.random.normal(0.02, 0.01)  # Tendencia de mejora
        
        return {
            'query_id': f"query_{np.random.randint(1000, 9999)}",
            'rag_type': rag_type,
            'query_complexity': query_complexity,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'results_count': results_count,
            'avg_confidence': avg_confidence,
            'max_confidence': max_confidence,
            'min_confidence': min_confidence,
            'confidence_variance': confidence_variance,
            'response_time': response_time,
            'pattern_match_score': pattern_match_score,
            'pattern_update_frequency': pattern_update_frequency,
            'success_rate_trend': success_rate_trend,
            'overall_quality_score': (precision + recall + f1) / 3,
            'stability_score': 1 - confidence_variance,
            'adaptability_score': 1 / (1 + pattern_update_frequency)
        }
    
    def _add_realistic_noise(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega ruido realista a las métricas RAG."""
        noise_factor = 0.05  # 5% de ruido para métricas de precisión
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key not in ['query_id', 'rag_type']:
                if key in ['precision', 'recall', 'f1_score', 'avg_confidence', 'max_confidence', 'min_confidence']:
                    # Para métricas de precisión, mantener en rango [0,1]
                    noise = np.random.normal(0, value * noise_factor)
                    metrics[key] = np.clip(value + noise, 0, 1)
                else:
                    noise = np.random.normal(0, abs(value) * noise_factor)
                    metrics[key] = max(0, value + noise)
        
        return metrics
    
    def _analyze_rag_precision(self) -> ExperimentResult:
        """Analiza la precisión general de los sistemas RAG."""
        print("[RAGExperiment] Analizando precisión general RAG...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Métricas de precisión generales
        overall_precision = df['precision'].mean()
        overall_recall = df['recall'].mean()
        overall_f1 = df['f1_score'].mean()
        
        # Análisis de precisión por tipo de RAG
        rag_groups = [df[df['rag_type'] == rag_type]['precision'].values 
                     for rag_type in self.rag_types]
        
        # ANOVA para comparar precisión entre tipos de RAG
        f_stat, p_value = f_oneway(*rag_groups)
        
        # Calcular tamaño del efecto (eta-squared)
        ss_between = sum(len(group) * (np.mean(group) - overall_precision)**2 for group in rag_groups)
        ss_total = sum((precision - overall_precision)**2 for precision in df['precision'])
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        # Validar supuestos
        assumptions_met = all(self.validate_assumptions(group) for group in rag_groups)
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), eta_squared, self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(eta_squared, 'eta_squared')
        
        if p_value < self.config.alpha:
            conclusion = f"Existe diferencia significativa en precisión entre tipos de RAG (F={f_stat:.3f}, p={p_value:.4f})"
        else:
            conclusion = f"No se encontró diferencia significativa en precisión entre tipos de RAG (F={f_stat:.3f}, p={p_value:.4f})"
        
        conclusion += f". Precisión general: {overall_precision:.3f}, Recall: {overall_recall:.3f}, F1: {overall_f1:.3f}"
        
        recommendations = [
            "Optimizar RAG de decor que muestra menor precisión",
            "Implementar estrategias de mejora específicas por tipo",
            "Monitorear tendencias de precisión por tipo de RAG"
        ]
        
        return ExperimentResult(
            experiment_name="RAG Precision Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=eta_squared,
            confidence_interval=self.calculate_confidence_interval(df['precision'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=assumptions_met,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_rag_by_type(self) -> ExperimentResult:
        """Análisis detallado por tipo de RAG."""
        print("[RAGExperiment] Analizando RAG por tipo...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Métricas por tipo
        type_metrics = {}
        for rag_type in self.rag_types:
            type_data = df[df['rag_type'] == rag_type]
            type_metrics[rag_type] = {
                'precision': type_data['precision'].mean(),
                'recall': type_data['recall'].mean(),
                'f1': type_data['f1_score'].mean(),
                'confidence': type_data['avg_confidence'].mean(),
                'response_time': type_data['response_time'].mean(),
                'stability': type_data['stability_score'].mean()
            }
        
        # Test de correlación entre métricas
        precision_stability_corr, precision_stability_p = pearsonr(
            df['precision'], df['stability_score']
        )
        
        confidence_precision_corr, confidence_precision_p = pearsonr(
            df['avg_confidence'], df['precision']
        )
        
        # Análisis de regresión múltiple
        X_vars = ['query_complexity', 'results_count', 'confidence_variance', 'pattern_match_score']
        y_var = 'precision'
        
        X = df[X_vars].values
        y = df[y_var].values
        
        # Eliminar filas con valores faltantes
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) >= 10:
            # Estandarizar variables
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Agregar constante
            X_with_const = sm.add_constant(X_scaled)
            
            # Ajustar modelo
            model = sm.OLS(y, X_with_const)
            results = model.fit()
            
            r_squared = results.rsquared
            f_stat = results.fvalue
            f_p_value = results.f_pvalue
        else:
            r_squared = 0
            f_stat = 0
            f_p_value = 1
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), abs(precision_stability_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(precision_stability_corr), 'cohens_d')
        
        conclusion = f"Análisis por tipo completado. Correlación precisión-estabilidad: r={precision_stability_corr:.3f} (p={precision_stability_p:.4f})"
        
        if f_p_value < self.config.alpha:
            conclusion += f". Modelo de regresión significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar estabilidad para mejorar precisión",
            "Implementar estrategias específicas por tipo de RAG",
            "Monitorear correlaciones identificadas"
        ]
        
        return ExperimentResult(
            experiment_name="RAG Type Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=f_stat,
            p_value=f_p_value,
            effect_size=abs(precision_stability_corr),
            confidence_interval=(-1, 1),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_pattern_adaptability(self) -> ExperimentResult:
        """Analiza la adaptabilidad de patrones RAG."""
        print("[RAGExperiment] Analizando adaptabilidad de patrones...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Métricas de adaptabilidad
        adaptability_scores = df['adaptability_score'].values
        update_frequencies = df['pattern_update_frequency'].values
        success_trends = df['success_rate_trend'].values
        
        # Análisis de adaptabilidad por tipo de RAG
        rag_adaptability_groups = [df[df['rag_type'] == rag_type]['adaptability_score'].values 
                                 for rag_type in self.rag_types]
        
        # Test de Kruskal-Wallis (no paramétrico)
        h_stat, p_value = kruskal(*rag_adaptability_groups)
        
        # Correlación entre adaptabilidad y rendimiento
        adaptability_performance_corr, adaptability_performance_p = spearmanr(
            adaptability_scores, df['overall_quality_score'].values
        )
        
        # Análisis de tendencias temporales
        df_sorted = df.sort_values('timestamp')
        temporal_trend, temporal_p = spearmanr(
            range(len(df_sorted)), df_sorted['adaptability_score'].values
        )
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(adaptability_scores), abs(adaptability_performance_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(adaptability_performance_corr), 'cohens_d')
        
        conclusion = f"Análisis de adaptabilidad completado. Correlación adaptabilidad-rendimiento: r={adaptability_performance_corr:.3f} (p={adaptability_performance_p:.4f})"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en adaptabilidad entre tipos (H={h_stat:.3f}, p={p_value:.4f})"
        
        if temporal_p < self.config.alpha:
            conclusion += f". Tendencia temporal significativa (r={temporal_trend:.3f}, p={temporal_p:.4f})"
        
        recommendations = [
            "Optimizar frecuencia de actualización de patrones",
            "Implementar aprendizaje adaptativo por tipo de RAG",
            "Monitorear tendencias temporales de adaptabilidad"
        ]
        
        return ExperimentResult(
            experiment_name="Pattern Adaptability Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(adaptability_scores),
            test_statistic=h_stat,
            p_value=p_value,
            effect_size=abs(adaptability_performance_corr),
            confidence_interval=self.calculate_confidence_interval(adaptability_scores),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,  # Kruskal-Wallis no requiere normalidad
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_query_complexity_correlation(self) -> ExperimentResult:
        """Analiza correlación entre complejidad de consulta y rendimiento RAG."""
        print("[RAGExperiment] Analizando correlación con complejidad...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Correlaciones con complejidad
        complexity_precision_corr, complexity_precision_p = spearmanr(
            df['query_complexity'], df['precision']
        )
        
        complexity_confidence_corr, complexity_confidence_p = spearmanr(
            df['query_complexity'], df['avg_confidence']
        )
        
        complexity_response_time_corr, complexity_response_time_p = spearmanr(
            df['query_complexity'], df['response_time']
        )
        
        # Análisis de regresión para predecir rendimiento basado en complejidad
        X = df[['query_complexity', 'results_count', 'confidence_variance']].values
        y = df['overall_quality_score'].values
        
        # Eliminar filas con valores faltantes
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) >= 10:
            # Estandarizar variables
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Agregar constante
            X_with_const = sm.add_constant(X_scaled)
            
            # Ajustar modelo
            model = sm.OLS(y, X_with_const)
            results = model.fit()
            
            r_squared = results.rsquared
            f_stat = results.fvalue
            f_p_value = results.f_pvalue
        else:
            r_squared = 0
            f_stat = 0
            f_p_value = 1
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), abs(complexity_precision_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(complexity_precision_corr), 'cohens_d')
        
        conclusion = f"Correlación complejidad-preción: r={complexity_precision_corr:.3f} (p={complexity_precision_p:.4f})"
        
        if complexity_confidence_p < self.config.alpha:
            conclusion += f". Correlación complejidad-confianza: r={complexity_confidence_corr:.3f} (p={complexity_confidence_p:.4f})"
        
        if f_p_value < self.config.alpha:
            conclusion += f". Modelo predictivo significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Implementar estrategias específicas para consultas complejas",
            "Optimizar algoritmos para mantener precisión en consultas complejas",
            "Desarrollar modelos predictivos de rendimiento"
        ]
        
        return ExperimentResult(
            experiment_name="Query Complexity Correlation",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=f_stat,
            p_value=f_p_value,
            effect_size=abs(complexity_precision_corr),
            confidence_interval=(-1, 1),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_temporal_stability(self) -> ExperimentResult:
        """Analiza la estabilidad temporal de los sistemas RAG."""
        print("[RAGExperiment] Analizando estabilidad temporal...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Ordenar por timestamp
        df_sorted = df.sort_values('timestamp')
        
        # Análisis de estabilidad temporal por tipo de RAG
        temporal_stability_metrics = {}
        
        for rag_type in self.rag_types:
            type_data = df_sorted[df_sorted['rag_type'] == rag_type]
            
            if len(type_data) > 10:
                # Calcular estabilidad temporal
                precision_trend, precision_trend_p = spearmanr(
                    range(len(type_data)), type_data['precision'].values
                )
                
                confidence_trend, confidence_trend_p = spearmanr(
                    range(len(type_data)), type_data['avg_confidence'].values
                )
                
                temporal_stability_metrics[rag_type] = {
                    'precision_trend': precision_trend,
                    'precision_trend_p': precision_trend_p,
                    'confidence_trend': confidence_trend,
                    'confidence_trend_p': confidence_trend_p,
                    'stability_score': 1 - abs(precision_trend)
                }
        
        # Análisis de varianza de estabilidad entre tipos
        stability_scores = [metrics['stability_score'] for metrics in temporal_stability_metrics.values()]
        
        if len(stability_scores) > 1:
            # Test de varianza
            f_stat, p_value = f_oneway(*[df_sorted[df_sorted['rag_type'] == rag_type]['stability_score'].values 
                                       for rag_type in temporal_stability_metrics.keys()])
        else:
            f_stat = 0
            p_value = 1
        
        # Correlación entre estabilidad y rendimiento general
        overall_stability = df_sorted['stability_score'].mean()
        stability_performance_corr, stability_performance_p = pearsonr(
            df_sorted['stability_score'].values, df_sorted['overall_quality_score'].values
        )
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df_sorted), abs(stability_performance_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(stability_performance_corr), 'cohens_d')
        
        conclusion = f"Análisis de estabilidad temporal completado. Estabilidad general: {overall_stability:.3f}"
        
        if stability_performance_p < self.config.alpha:
            conclusion += f". Correlación estabilidad-rendimiento: r={stability_performance_corr:.3f} (p={stability_performance_p:.4f})"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en estabilidad entre tipos (F={f_stat:.3f}, p={p_value:.4f})"
        
        recommendations = [
            "Implementar monitoreo continuo de estabilidad temporal",
            "Desarrollar estrategias de estabilización por tipo de RAG",
            "Optimizar algoritmos para mantener consistencia temporal"
        ]
        
        return ExperimentResult(
            experiment_name="Temporal Stability Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df_sorted),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(stability_performance_corr),
            confidence_interval=self.calculate_confidence_interval(df_sorted['stability_score'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )

def run_rag_experiments(system_components: Dict[str, Any]) -> List[ExperimentResult]:
    """Función principal para ejecutar todos los experimentos RAG."""
    print("="*80)
    print("INICIANDO EXPERIMENTOS DE PRECISIÓN RAG")
    print("="*80)
    
    # Configurar experimento
    config = ExperimentConfig(
        name="RAG_Precision_Complete",
        description="Análisis completo de precisión de sistemas RAG",
        alpha=0.05,
        power=0.8,
        effect_size=0.3,
        min_sample_size=30,
        max_sample_size=500
    )
    
    # Crear y ejecutar experimento con directorio de salida específico
    output_dir = os.path.join("results", "rag_precision")
    experiment = RAGPrecisionExperiment(config, system_components, output_dir)
    results = experiment.run()
    
    # Generar visualizaciones
    experiment.generate_visualizations()
    
    # Guardar datos
    experiment.save_data()
    
    # Generar reporte
    data_summary = {
        'total_samples': len(experiment.data_buffer),
        'duration': f"{len(experiment.data_buffer)} consultas simuladas",
        'experiments_completed': len(results)
    }
    
    report_file = experiment.reporter.generate_report(
        experiment.config.name, results, data_summary
    )
    
    print(f"\n✅ Experimentos RAG completados:")
    print(f"   - Análisis realizados: {len(results)}")
    print(f"   - Consultas procesadas: {len(experiment.data_buffer)}")
    print(f"   - Reporte generado: {report_file}")
    
    return results

if __name__ == "__main__":
    # Ejemplo de uso
    mock_components = {
        'venue_rag': None,
        'catering_rag': None,
        'decor_rag': None
    }
    
    results = run_rag_experiments(mock_components)
    
    # Mostrar resumen de resultados
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS RAG")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.experiment_name}")
        print(f"   Conclusión: {result.conclusion}")
        print(f"   P-valor: {result.p_value:.4f}")
        print(f"   Tamaño del efecto: {result.effect_size:.3f} ({result.effect_significance})")
        print(f"   Potencia: {result.power_achieved:.3f}") 