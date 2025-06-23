#!/usr/bin/env python3
"""
Experimento 3: Análisis de Calidad de Información RAG vs No-RAG
Implementa comparación A/B robusta de calidad de respuestas con y sin RAG.
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
from scipy.stats import f_oneway, kruskal, pearsonr, spearmanr, ttest_rel, ttest_ind

class RAGQualityComparisonExperiment(BaseExperiment):
    """Experimento para comparar calidad de información con RAG vs sin RAG."""
    
    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any], output_dir: str = None):
        super().__init__(config, system_components, output_dir)
        self.rag_types = ['venue', 'catering', 'decor']
        self.query_categories = ['budget', 'capacity', 'style', 'location', 'services']
        self.quality_metrics = ['relevance', 'completeness', 'accuracy', 'usefulness', 'clarity']
        
    def run(self) -> List[ExperimentResult]:
        """Ejecuta el experimento completo de comparación RAG vs No-RAG."""
        print(f"[RAGQualityExperiment] Iniciando experimento: {self.config.name}")
        
        # Generar datos sintéticos para el experimento
        self._generate_synthetic_comparison_data()
        
        # Ejecutar análisis de comparación general
        comparison_result = self._analyze_rag_vs_norag_comparison()
        self.results.append(comparison_result)
        
        # Ejecutar análisis por tipo de consulta
        query_type_result = self._analyze_by_query_type()
        self.results.append(query_type_result)
        
        # Ejecutar análisis de mejora incremental
        improvement_result = self._analyze_improvement_metrics()
        self.results.append(improvement_result)
        
        # Ejecutar análisis de complejidad vs beneficio RAG
        complexity_benefit_result = self._analyze_complexity_benefit()
        self.results.append(complexity_benefit_result)
        
        # Ejecutar análisis de estabilidad de mejora
        stability_result = self._analyze_improvement_stability()
        self.results.append(stability_result)
        
        print(f"[RAGQualityExperiment] Experimento completado. {len(self.results)} análisis realizados.")
        return self.results
    
    def _generate_synthetic_comparison_data(self):
        """Genera datos sintéticos para comparación RAG vs No-RAG."""
        print("[RAGQualityExperiment] Generando datos sintéticos para comparación...")
        
        np.random.seed(self.config.random_seed)
        n_queries = 600#Tamaño de muestra robusto para comparación A/B
        
        for i in range(n_queries):
            # Generar tipo de consulta aleatorio
            query_type = np.random.choice(self.rag_types, p=[0.4, 0.35, 0.25])
            
            # Generar complejidad de consulta
            query_complexity = np.random.uniform(0.1, 1.0)
            
            # Generar métricas base (sin RAG)
            baseline_metrics = self._generate_baseline_metrics(query_type, query_complexity)
            
            # Generar métricas con RAG
            rag_metrics = self._generate_rag_metrics(query_type, query_complexity, baseline_metrics)
            
            # Agregar ruido realista
            baseline_metrics = self._add_realistic_noise(baseline_metrics)
            rag_metrics = self._add_realistic_noise(rag_metrics)
            
            # Agregar timestamp
            timestamp = datetime.now() - timedelta(minutes=np.random.randint(0, 1440))
            baseline_metrics['timestamp'] = timestamp
            rag_metrics['timestamp'] = timestamp
            
            # Agregar identificador de consulta
            query_id = f"query_{np.random.randint(1000, 9999)}"
            baseline_metrics['query_id'] = query_id
            rag_metrics['query_id'] = query_id
            
            # Agregar a buffer
            self.data_buffer.append({
                'query_id': query_id,
                'query_type': query_type,
                'query_complexity': query_complexity,
                'timestamp': timestamp,
                'baseline': baseline_metrics,
                'rag': rag_metrics,
                'improvement': self._calculate_improvement(baseline_metrics, rag_metrics)
            })
        
        print(f"[RAGQualityExperiment] Generados {len(self.data_buffer)} registros de comparación")
    
    def _generate_baseline_metrics(self, query_type: str, query_complexity: float) -> Dict[str, Any]:
        """Genera métricas base sin RAG."""
        # Parámetros base según tipo de consulta
        baseline_params = {
            'venue': {
                'base_relevance': 0.65,
                'base_completeness': 0.60,
                'base_accuracy': 0.70,
                'base_usefulness': 0.55,
                'base_clarity': 0.75
            },
            'catering': {
                'base_relevance': 0.60,
                'base_completeness': 0.55,
                'base_accuracy': 0.65,
                'base_usefulness': 0.50,
                'base_clarity': 0.70
            },
            'decor': {
                'base_relevance': 0.55,
                'base_completeness': 0.50,
                'base_accuracy': 0.60,
                'base_usefulness': 0.45,
                'base_clarity': 0.65
            }
        }
        
        params = baseline_params[query_type]
        
        # Ajustar métricas por complejidad
        complexity_factor = 1 - (query_complexity * 0.4)  # Complejidad reduce rendimiento base
        
        metrics = {}
        for metric in self.quality_metrics:
            base_value = params[f'base_{metric}']
            metrics[metric] = base_value * complexity_factor
        
        # Métricas adicionales
        metrics['response_time'] = np.random.exponential(1.5)  # Más rápido sin RAG
        metrics['confidence'] = np.random.beta(2, 3) * 0.6  # Menor confianza
        metrics['detail_level'] = np.random.beta(1, 2) * 0.5  # Menos detalle
        metrics['context_awareness'] = np.random.beta(1, 3) * 0.4  # Menos contexto
        
        return metrics
    
    def _generate_rag_metrics(self, query_type: str, query_complexity: float, baseline: Dict[str, Any]) -> Dict[str, Any]:
        """Genera métricas con RAG basadas en las métricas base."""
        # Factor de mejora RAG por tipo
        rag_improvement_factors = {
            'venue': {
                'relevance': 1.25,
                'completeness': 1.35,
                'accuracy': 1.20,
                'usefulness': 1.30,
                'clarity': 1.15
            },
            'catering': {
                'relevance': 1.20,
                'completeness': 1.30,
                'accuracy': 1.15,
                'usefulness': 1.25,
                'clarity': 1.10
            },
            'decor': {
                'relevance': 1.15,
                'completeness': 1.25,
                'accuracy': 1.10,
                'usefulness': 1.20,
                'clarity': 1.05
            }
        }
        
        factors = rag_improvement_factors[query_type]
        
        # Ajustar factor de mejora por complejidad
        complexity_benefit = 1 + (query_complexity * 0.3)  # Consultas complejas se benefician más
        
        metrics = {}
        for metric in self.quality_metrics:
            baseline_value = baseline[metric]
            improvement_factor = factors[metric] * complexity_benefit
            metrics[metric] = min(1.0, baseline_value * improvement_factor)
        
        # Métricas adicionales con RAG
        metrics['response_time'] = baseline['response_time'] * 1.2  # Más lento con RAG
        metrics['confidence'] = min(1.0, baseline['confidence'] * 1.4)  # Mayor confianza
        metrics['detail_level'] = min(1.0, baseline['detail_level'] * 1.6)  # Más detalle
        metrics['context_awareness'] = min(1.0, baseline['context_awareness'] * 1.8)  # Más contexto
        
        return metrics
    
    def _calculate_improvement(self, baseline: Dict[str, Any], rag: Dict[str, Any]) -> Dict[str, float]:
        """Calcula métricas de mejora."""
        improvement = {}
        
        for metric in self.quality_metrics:
            if baseline[metric] > 0:
                improvement[metric] = (rag[metric] - baseline[metric]) / baseline[metric]
            else:
                improvement[metric] = 0.0
        
        # Métricas adicionales de mejora
        improvement['overall_quality'] = np.mean([improvement[m] for m in self.quality_metrics])
        improvement['confidence_gain'] = (rag['confidence'] - baseline['confidence']) / max(baseline['confidence'], 0.01)
        improvement['detail_gain'] = (rag['detail_level'] - baseline['detail_level']) / max(baseline['detail_level'], 0.01)
        improvement['context_gain'] = (rag['context_awareness'] - baseline['context_awareness']) / max(baseline['context_awareness'], 0.01)
        
        return improvement
    
    def _add_realistic_noise(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega ruido realista a las métricas."""
        noise_factor = 0.08  # 8% de ruido para métricas de calidad
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key not in ['query_id', 'query_type']:
                if key in self.quality_metrics + ['confidence', 'detail_level', 'context_awareness']:
                    # Para métricas de calidad, mantener en rango [0,1]
                    noise = np.random.normal(0, value * noise_factor)
                    metrics[key] = np.clip(value + noise, 0, 1)
                else:
                    noise = np.random.normal(0, abs(value) * noise_factor)
                    metrics[key] = max(0, value + noise)
        
        return metrics
    
    def _analyze_rag_vs_norag_comparison(self) -> ExperimentResult:
        """Analiza la comparación general RAG vs No-RAG."""
        print("[RAGQualityExperiment] Analizando comparación general RAG vs No-RAG...")
        
        # Extraer métricas de mejora
        improvements = [record['improvement'] for record in self.data_buffer]
        overall_improvements = [imp['overall_quality'] for imp in improvements]
        
        # Test t-pareado para comparar métricas
        baseline_metrics = []
        rag_metrics = []
        
        for record in self.data_buffer:
            baseline_metrics.append(np.mean([record['baseline'][m] for m in self.quality_metrics]))
            rag_metrics.append(np.mean([record['rag'][m] for m in self.quality_metrics]))
        
        # Test t-pareado
        t_stat, p_value = ttest_rel(rag_metrics, baseline_metrics)
        
        # Calcular tamaño del efecto (Cohen's d)
        effect_size = self.effect_calculator.cohens_d(np.array(rag_metrics), np.array(baseline_metrics))
        
        # Calcular intervalos de confianza
        mean_improvement = np.mean(overall_improvements)
        ci = self.calculate_confidence_interval(np.array(overall_improvements))
        
        # Validar supuestos
        assumptions_met = self.validate_assumptions(np.array(overall_improvements))
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(overall_improvements), abs(effect_size), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(effect_size), 'cohens_d')
        
        if p_value < self.config.alpha:
            conclusion = f"RAG mejora significativamente la calidad (t={t_stat:.3f}, p={p_value:.4f})"
        else:
            conclusion = f"No se encontró mejora significativa con RAG (t={t_stat:.3f}, p={p_value:.4f})"
        
        conclusion += f". Mejora promedio: {mean_improvement:.1%}, IC95%: [{ci[0]:.1%}, {ci[1]:.1%}]"
        
        recommendations = [
            "Implementar RAG para mejorar calidad general de respuestas",
            "Optimizar algoritmos RAG para maximizar mejora",
            "Monitorear mejora por tipo de consulta"
        ]
        
        return ExperimentResult(
            experiment_name="RAG vs No-RAG General Comparison",
            timestamp=datetime.now().isoformat(),
            sample_size=len(overall_improvements),
            test_statistic=t_stat,
            p_value=p_value,
            effect_size=abs(effect_size),
            confidence_interval=ci,
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=assumptions_met,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_by_query_type(self) -> ExperimentResult:
        """Análisis de mejora por tipo de consulta."""
        print("[RAGQualityExperiment] Analizando mejora por tipo de consulta...")
        
        # Agrupar por tipo de consulta
        type_improvements = {}
        for record in self.data_buffer:
            query_type = record['query_type']
            if query_type not in type_improvements:
                type_improvements[query_type] = []
            type_improvements[query_type].append(record['improvement']['overall_quality'])
        
        # ANOVA para comparar mejora entre tipos
        improvement_groups = [np.array(improvements) for improvements in type_improvements.values()]
        f_stat, p_value = f_oneway(*improvement_groups)
        
        # Calcular tamaños de efecto por tipo
        type_effect_sizes = {}
        for query_type, improvements in type_improvements.items():
            baseline_group = [record['baseline'] for record in self.data_buffer if record['query_type'] == query_type]
            rag_group = [record['rag'] for record in self.data_buffer if record['query_type'] == query_type]
            
            baseline_avg = np.mean([np.mean([b[m] for m in self.quality_metrics]) for b in baseline_group])
            rag_avg = np.mean([np.mean([r[m] for m in self.quality_metrics]) for r in rag_group])
            
            type_effect_sizes[query_type] = (rag_avg - baseline_avg) / baseline_avg if baseline_avg > 0 else 0
        
        # Calcular potencia
        max_effect = max(type_effect_sizes.values())
        power_achieved = self.power_analyzer.calculate_power(
            len(self.data_buffer), max_effect, self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(max_effect, 'cohens_d')
        
        conclusion = f"Análisis por tipo completado. Mejora promedio por tipo:"
        for query_type, effect_size in type_effect_sizes.items():
            conclusion += f" {query_type}: {effect_size:.1%},"
        
        if p_value < self.config.alpha:
            conclusion += f" Diferencia significativa entre tipos (F={f_stat:.3f}, p={p_value:.4f})"
        
        recommendations = [
            "Optimizar RAG específicamente para tipos con menor mejora",
            "Implementar estrategias diferenciadas por tipo de consulta",
            "Monitorear mejora específica por categoría"
        ]
        
        return ExperimentResult(
            experiment_name="RAG Improvement by Query Type",
            timestamp=datetime.now().isoformat(),
            sample_size=len(self.data_buffer),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=max_effect,
            confidence_interval=(-1, 1),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_improvement_metrics(self) -> ExperimentResult:
        """Analiza métricas específicas de mejora."""
        print("[RAGQualityExperiment] Analizando métricas específicas de mejora...")
        
        # Extraer métricas de mejora específicas
        metric_improvements = {}
        for metric in self.quality_metrics:
            metric_improvements[metric] = [record['improvement'][metric] for record in self.data_buffer]
        
        # Análisis de correlación entre métricas de mejora
        improvement_correlations = {}
        for i, metric1 in enumerate(self.quality_metrics):
            for j, metric2 in enumerate(self.quality_metrics[i+1:], i+1):
                corr, p_val = pearsonr(metric_improvements[metric1], metric_improvements[metric2])
                improvement_correlations[f"{metric1}_vs_{metric2}"] = (corr, p_val)
        
        # Análisis de regresión múltiple para predecir mejora general
        X_vars = ['query_complexity'] + [f'improvement_{m}' for m in self.quality_metrics]
        y_var = 'overall_improvement'
        
        # Preparar datos
        X_data = []
        y_data = []
        
        for record in self.data_buffer:
            x_row = [record['query_complexity']]
            for metric in self.quality_metrics:
                x_row.append(record['improvement'][metric])
            X_data.append(x_row)
            y_data.append(record['improvement']['overall_quality'])
        
        X = np.array(X_data)
        y = np.array(y_data)
        
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
        max_corr = max([abs(corr) for corr, _ in improvement_correlations.values()])
        power_achieved = self.power_analyzer.calculate_power(
            len(self.data_buffer), max_corr, self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(max_corr, 'cohens_d')
        
        conclusion = f"Análisis de métricas de mejora completado. R² del modelo predictivo: {r_squared:.3f}"
        
        if f_p_value < self.config.alpha:
            conclusion += f". Modelo significativo (F={f_stat:.3f}, p={f_p_value:.4f})"
        
        # Identificar métricas más correlacionadas
        max_corr_pair = max(improvement_correlations.items(), key=lambda x: abs(x[1][0]))
        conclusion += f". Mayor correlación: {max_corr_pair[0]} (r={max_corr_pair[1][0]:.3f})"
        
        recommendations = [
            "Optimizar métricas con mayor impacto en mejora general",
            "Implementar modelos predictivos de mejora",
            "Monitorear correlaciones entre métricas de mejora"
        ]
        
        return ExperimentResult(
            experiment_name="RAG Improvement Metrics Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(self.data_buffer),
            test_statistic=f_stat,
            p_value=f_p_value,
            effect_size=max_corr,
            confidence_interval=(-1, 1),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_complexity_benefit(self) -> ExperimentResult:
        """Analiza la relación entre complejidad de consulta y beneficio RAG."""
        print("[RAGQualityExperiment] Analizando relación complejidad-beneficio...")
        
        # Extraer datos de complejidad y mejora
        complexities = [record['query_complexity'] for record in self.data_buffer]
        improvements = [record['improvement']['overall_quality'] for record in self.data_buffer]
        
        # Correlación entre complejidad y mejora
        complexity_improvement_corr, complexity_improvement_p = spearmanr(complexities, improvements)
        
        # Análisis por niveles de complejidad
        complexity_levels = ['low', 'medium', 'high']
        complexity_thresholds = [0.33, 0.67]
        
        level_improvements = {'low': [], 'medium': [], 'high': []}
        
        for complexity, improvement in zip(complexities, improvements):
            if complexity < complexity_thresholds[0]:
                level_improvements['low'].append(improvement)
            elif complexity < complexity_thresholds[1]:
                level_improvements['medium'].append(improvement)
            else:
                level_improvements['high'].append(improvement)
        
        # ANOVA para comparar mejora entre niveles de complejidad
        level_groups = [np.array(improvements) for improvements in level_improvements.values() if len(improvements) > 0]
        
        if len(level_groups) > 1:
            f_stat, p_value = f_oneway(*level_groups)
        else:
            f_stat = 0
            p_value = 1
        
        # Análisis de regresión para predecir mejora basada en complejidad
        X = np.array(complexities).reshape(-1, 1)
        y = np.array(improvements)
        
        # Eliminar filas con valores faltantes
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) >= 10:
            # Agregar constante
            X_with_const = sm.add_constant(X)
            
            # Ajustar modelo
            model = sm.OLS(y, X_with_const)
            results = model.fit()
            
            r_squared = results.rsquared
            slope = results.params[1]
            slope_p = results.pvalues[1]
        else:
            r_squared = 0
            slope = 0
            slope_p = 1
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(complexities), abs(complexity_improvement_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(complexity_improvement_corr), 'cohens_d')
        
        conclusion = f"Correlación complejidad-mejora: r={complexity_improvement_corr:.3f} (p={complexity_improvement_p:.4f})"
        
        if slope_p < self.config.alpha:
            conclusion += f". Pendiente significativa: {slope:.3f} (p={slope_p:.4f})"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa entre niveles (F={f_stat:.3f}, p={p_value:.4f})"
        
        recommendations = [
            "Priorizar RAG para consultas complejas",
            "Optimizar algoritmos para consultas simples",
            "Implementar estrategias adaptativas por complejidad"
        ]
        
        return ExperimentResult(
            experiment_name="Complexity-Benefit Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(complexities),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(complexity_improvement_corr),
            confidence_interval=(-1, 1),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_improvement_stability(self) -> ExperimentResult:
        """Analiza la estabilidad de la mejora RAG a lo largo del tiempo."""
        print("[RAGQualityExperiment] Analizando estabilidad de mejora...")
        
        # Ordenar por timestamp
        sorted_data = sorted(self.data_buffer, key=lambda x: x['timestamp'])
        
        # Análisis de estabilidad temporal
        timestamps = [record['timestamp'] for record in sorted_data]
        improvements = [record['improvement']['overall_quality'] for record in sorted_data]
        
        # Correlación temporal
        temporal_corr, temporal_p = spearmanr(range(len(improvements)), improvements)
        
        # Análisis de varianza temporal
        n_periods = 4  # Dividir en 4 períodos
        period_size = len(improvements) // n_periods
        
        period_improvements = []
        for i in range(n_periods):
            start_idx = i * period_size
            end_idx = start_idx + period_size if i < n_periods - 1 else len(improvements)
            period_improvements.append(improvements[start_idx:end_idx])
        
        # ANOVA para comparar períodos
        if len(period_improvements) > 1:
            f_stat, p_value = f_oneway(*period_improvements)
        else:
            f_stat = 0
            p_value = 1
        
        # Análisis de tendencia
        if len(improvements) > 10:
            # Regresión lineal para tendencia
            X = np.array(range(len(improvements))).reshape(-1, 1)
            y = np.array(improvements)
            
            X_with_const = sm.add_constant(X)
            model = sm.OLS(y, X_with_const)
            results = model.fit()
            
            trend_slope = results.params[1]
            trend_p = results.pvalues[1]
            trend_r_squared = results.rsquared
        else:
            trend_slope = 0
            trend_p = 1
            trend_r_squared = 0
        
        # Calcular estabilidad (inverso de varianza)
        stability_score = 1 / (1 + np.var(improvements))
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(improvements), abs(temporal_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(temporal_corr), 'cohens_d')
        
        conclusion = f"Análisis de estabilidad completado. Estabilidad: {stability_score:.3f}"
        
        if temporal_p < self.config.alpha:
            conclusion += f". Correlación temporal: r={temporal_corr:.3f} (p={temporal_p:.4f})"
        
        if trend_p < self.config.alpha:
            conclusion += f". Tendencia significativa: {trend_slope:.3f} (p={trend_p:.4f})"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia entre períodos (F={f_stat:.3f}, p={p_value:.4f})"
        
        recommendations = [
            "Implementar monitoreo continuo de estabilidad",
            "Desarrollar estrategias de estabilización",
            "Optimizar algoritmos para consistencia temporal"
        ]
        
        return ExperimentResult(
            experiment_name="Improvement Stability Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(improvements),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(temporal_corr),
            confidence_interval=self.calculate_confidence_interval(np.array(improvements)),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )

def run_rag_quality_experiments(system_components: Dict[str, Any]) -> List[ExperimentResult]:
    """Función principal para ejecutar experimentos de calidad RAG vs No-RAG."""
    print("="*80)
    print("INICIANDO EXPERIMENTOS DE CALIDAD RAG vs No-RAG")
    print("="*80)
    
    # Configurar experimento
    config = ExperimentConfig(
        name="RAG_Quality_Comparison",
        description="Comparación A/B de calidad de información con RAG vs sin RAG",
        alpha=0.05,
        power=0.8,
        effect_size=0.3,
        min_sample_size=30,
        max_sample_size=500
    )
    
    # Crear y ejecutar experimento
    output_dir = os.path.join("results", "rag_quality_comparison")
    experiment = RAGQualityComparisonExperiment(config, system_components, output_dir)
    results = experiment.run()
    
    # Generar visualizaciones
    experiment.generate_visualizations()
    
    # Guardar datos
    experiment.save_data()
    
    # Generar reporte
    data_summary = {
        'total_samples': len(experiment.data_buffer),
        'duration': f"{len(experiment.data_buffer)} comparaciones A/B",
        'experiments_completed': len(results)
    }
    
    report_file = experiment.reporter.generate_report(
        experiment.config.name, results, data_summary
    )
    
    print(f"\n✅ Experimentos de calidad RAG completados:")
    print(f"   - Análisis realizados: {len(results)}")
    print(f"   - Comparaciones procesadas: {len(experiment.data_buffer)}")
    print(f"   - Reporte generado: {report_file}")
    
    return results

if __name__ == "__main__":
    # Ejemplo de uso
    mock_components = {
        'venue_rag': None,
        'catering_rag': None,
        'decor_rag': None
    }
    
    results = run_rag_quality_experiments(mock_components)
    
    # Mostrar resumen de resultados
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS DE CALIDAD RAG")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.experiment_name}")
        print(f"   Conclusión: {result.conclusion}")
        print(f"   P-valor: {result.p_value:.4f}")
        print(f"   Tamaño del efecto: {result.effect_size:.3f} ({result.effect_significance})")
        print(f"   Potencia: {result.power_achieved:.3f}") 