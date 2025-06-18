#!/usr/bin/env python3
"""
Experimento 5: Análisis de Rendimiento del Sistema
Implementa análisis robusto de escalabilidad y distribución de presupuesto.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import os
import psutil
import time
from framework.experimental_framework import BaseExperiment, ExperimentConfig, ExperimentResult
from framework.experimental_framework import StatisticalValidator, EffectSizeCalculator, PowerAnalyzer
from scipy.stats import chi2_contingency, ks_2samp
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import statsmodels.api as sm
from scipy.stats import f_oneway, kruskal, pearsonr, spearmanr

class SystemPerformanceExperiment(BaseExperiment):
    """Experimento para analizar el rendimiento del sistema."""
    
    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any], output_dir: str = None):
        super().__init__(config, system_components, output_dir)
        self.load_scenarios = ['low', 'medium', 'high', 'extreme']
        self.budget_ranges = ['low', 'medium', 'high', 'luxury']
        
    def run(self) -> List[ExperimentResult]:
        """Ejecuta el experimento completo de rendimiento del sistema."""
        print(f"[PerformanceExperiment] Iniciando experimento: {self.config.name}")
        
        # Generar datos sintéticos para el experimento
        self._generate_synthetic_performance_data()
        
        # Ejecutar análisis de escalabilidad
        scalability_result = self._analyze_system_scalability()
        self.results.append(scalability_result)
        
        # Ejecutar análisis de distribución de presupuesto
        budget_result = self._analyze_budget_distribution()
        self.results.append(budget_result)
        
        # Ejecutar análisis de uso de recursos
        resource_result = self._analyze_resource_usage()
        self.results.append(resource_result)
        
        # Ejecutar análisis de throughput
        throughput_result = self._analyze_throughput_performance()
        self.results.append(throughput_result)
        
        # Ejecutar análisis de latencia
        latency_result = self._analyze_latency_performance()
        self.results.append(latency_result)
        
        print(f"[PerformanceExperiment] Experimento completado. {len(self.results)} análisis realizados.")
        return self.results
    
    def _generate_synthetic_performance_data(self):
        """Genera datos sintéticos realistas para el experimento de rendimiento."""
        print("[PerformanceExperiment] Generando datos sintéticos de rendimiento...")
        
        np.random.seed(self.config.random_seed)
        n_operations = 400  # Tamaño de muestra robusto
        
        for i in range(n_operations):
            # Generar escenario de carga aleatorio
            load_scenario = np.random.choice(self.load_scenarios, p=[0.4, 0.3, 0.2, 0.1])
            
            # Generar rango de presupuesto aleatorio
            budget_range = np.random.choice(self.budget_ranges, p=[0.3, 0.4, 0.2, 0.1])
            
            # Generar métricas de rendimiento basadas en escenario
            performance_metrics = self._generate_performance_metrics(load_scenario, budget_range)
            
            # Agregar ruido realista
            performance_metrics = self._add_realistic_noise(performance_metrics)
            
            # Agregar timestamp
            performance_metrics['timestamp'] = datetime.now() - timedelta(
                minutes=np.random.randint(0, 1440)  # Últimas 24 horas
            )
            
            self.data_buffer.append(performance_metrics)
        
        print(f"[PerformanceExperiment] Generados {len(self.data_buffer)} registros de datos de rendimiento")
    
    def _generate_performance_metrics(self, load_scenario: str, budget_range: str) -> Dict[str, Any]:
        """Genera métricas de rendimiento basadas en escenario de carga y presupuesto."""
        # Parámetros base según escenario de carga
        load_params = {
            'low': {
                'concurrent_sessions': np.random.poisson(5),
                'graph_size_nodes': np.random.poisson(1000),
                'memory_usage_mb': np.random.exponential(50.0),
                'cpu_usage_percent': np.random.exponential(10.0),
                'response_time_ms': np.random.exponential(500.0),
                'throughput_ops_per_sec': np.random.exponential(10.0)
            },
            'medium': {
                'concurrent_sessions': np.random.poisson(15),
                'graph_size_nodes': np.random.poisson(5000),
                'memory_usage_mb': np.random.exponential(150.0),
                'cpu_usage_percent': np.random.exponential(25.0),
                'response_time_ms': np.random.exponential(1000.0),
                'throughput_ops_per_sec': np.random.exponential(25.0)
            },
            'high': {
                'concurrent_sessions': np.random.poisson(30),
                'graph_size_nodes': np.random.poisson(10000),
                'memory_usage_mb': np.random.exponential(300.0),
                'cpu_usage_percent': np.random.exponential(50.0),
                'response_time_ms': np.random.exponential(2000.0),
                'throughput_ops_per_sec': np.random.exponential(40.0)
            },
            'extreme': {
                'concurrent_sessions': np.random.poisson(50),
                'graph_size_nodes': np.random.poisson(20000),
                'memory_usage_mb': np.random.exponential(600.0),
                'cpu_usage_percent': np.random.exponential(80.0),
                'response_time_ms': np.random.exponential(5000.0),
                'throughput_ops_per_sec': np.random.exponential(60.0)
            }
        }
        
        # Parámetros de distribución de presupuesto
        budget_params = {
            'low': {
                'budget_total': np.random.uniform(5000, 15000),
                'venue_percentage': np.random.uniform(0.4, 0.6),
                'catering_percentage': np.random.uniform(0.25, 0.4),
                'decor_percentage': np.random.uniform(0.15, 0.3),
                'distribution_efficiency': np.random.uniform(0.7, 0.9),
                'user_satisfaction': np.random.uniform(0.6, 0.8)
            },
            'medium': {
                'budget_total': np.random.uniform(15000, 35000),
                'venue_percentage': np.random.uniform(0.35, 0.55),
                'catering_percentage': np.random.uniform(0.3, 0.45),
                'decor_percentage': np.random.uniform(0.2, 0.35),
                'distribution_efficiency': np.random.uniform(0.8, 0.95),
                'user_satisfaction': np.random.uniform(0.75, 0.9)
            },
            'high': {
                'budget_total': np.random.uniform(35000, 75000),
                'venue_percentage': np.random.uniform(0.3, 0.5),
                'catering_percentage': np.random.uniform(0.35, 0.5),
                'decor_percentage': np.random.uniform(0.25, 0.4),
                'distribution_efficiency': np.random.uniform(0.85, 0.98),
                'user_satisfaction': np.random.uniform(0.8, 0.95)
            },
            'luxury': {
                'budget_total': np.random.uniform(75000, 200000),
                'venue_percentage': np.random.uniform(0.25, 0.45),
                'catering_percentage': np.random.uniform(0.4, 0.55),
                'decor_percentage': np.random.uniform(0.3, 0.45),
                'distribution_efficiency': np.random.uniform(0.9, 1.0),
                'user_satisfaction': np.random.uniform(0.85, 0.98)
            }
        }
        
        load_data = load_params[load_scenario]
        budget_data = budget_params[budget_range]
        
        # Calcular métricas derivadas
        total_percentage = (budget_data['venue_percentage'] + 
                          budget_data['catering_percentage'] + 
                          budget_data['decor_percentage'])
        
        # Normalizar porcentajes si no suman 1
        if total_percentage != 1.0:
            budget_data['venue_percentage'] /= total_percentage
            budget_data['catering_percentage'] /= total_percentage
            budget_data['decor_percentage'] /= total_percentage
        
        # Calcular presupuestos específicos
        venue_budget = budget_data['budget_total'] * budget_data['venue_percentage']
        catering_budget = budget_data['budget_total'] * budget_data['catering_percentage']
        decor_budget = budget_data['budget_total'] * budget_data['decor_percentage']
        
        # Calcular eficiencia del sistema
        system_efficiency = 1 - (load_data['response_time_ms'] / 10000)  # Normalizado
        resource_efficiency = 1 - (load_data['memory_usage_mb'] / 1000)  # Normalizado
        
        return {
            'operation_id': f"op_{np.random.randint(1000, 9999)}",
            'load_scenario': load_scenario,
            'budget_range': budget_range,
            'concurrent_sessions': load_data['concurrent_sessions'],
            'graph_size_nodes': load_data['graph_size_nodes'],
            'memory_usage_mb': load_data['memory_usage_mb'],
            'cpu_usage_percent': load_data['cpu_usage_percent'],
            'response_time_ms': load_data['response_time_ms'],
            'throughput_ops_per_sec': load_data['throughput_ops_per_sec'],
            'budget_total': budget_data['budget_total'],
            'venue_budget': venue_budget,
            'catering_budget': catering_budget,
            'decor_budget': decor_budget,
            'venue_percentage': budget_data['venue_percentage'],
            'catering_percentage': budget_data['catering_percentage'],
            'decor_percentage': budget_data['decor_percentage'],
            'distribution_efficiency': budget_data['distribution_efficiency'],
            'user_satisfaction': budget_data['user_satisfaction'],
            'system_efficiency': system_efficiency,
            'resource_efficiency': resource_efficiency,
            'overall_performance_score': (system_efficiency + resource_efficiency + budget_data['distribution_efficiency']) / 3
        }
    
    def _add_realistic_noise(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega ruido realista a las métricas de rendimiento."""
        noise_factor = 0.08  # 8% de ruido para métricas de rendimiento
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key not in ['operation_id', 'load_scenario', 'budget_range']:
                # Asegurar que el valor sea positivo para evitar problemas con np.random.normal
                safe_value = max(abs(value), 0.001)  # Mínimo 0.001 para evitar división por cero
                
                if key in ['system_efficiency', 'resource_efficiency', 'distribution_efficiency', 'user_satisfaction']:
                    # Para métricas de eficiencia, mantener en rango [0,1]
                    noise = np.random.normal(0, safe_value * noise_factor)
                    metrics[key] = np.clip(value + noise, 0, 1)
                else:
                    # Para otras métricas, asegurar que no sean negativas
                    noise = np.random.normal(0, safe_value * noise_factor)
                    metrics[key] = max(0, value + noise)
        
        return metrics
    
    def _analyze_system_scalability(self) -> ExperimentResult:
        """Analiza la escalabilidad del sistema."""
        print("[PerformanceExperiment] Analizando escalabilidad del sistema...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Análisis de escalabilidad por escenario de carga
        load_groups = [df[df['load_scenario'] == scenario]['overall_performance_score'].values 
                      for scenario in self.load_scenarios]
        
        # ANOVA para comparar rendimiento entre escenarios de carga
        f_stat, p_value = f_oneway(*load_groups)
        
        # Calcular tamaño del efecto (eta-squared)
        overall_performance = df['overall_performance_score'].mean()
        ss_between = sum(len(group) * (np.mean(group) - overall_performance)**2 for group in load_groups)
        ss_total = sum((score - overall_performance)**2 for score in df['overall_performance_score'])
        eta_squared = ss_between / ss_total if ss_total > 0 else 0
        
        # Análisis de regresión polinomial para escalabilidad
        X = df[['concurrent_sessions', 'graph_size_nodes']].values
        y = df['response_time_ms'].values
        
        # Eliminar filas con valores faltantes
        mask = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[mask]
        y = y[mask]
        
        if len(X) >= 10:
            # Transformación polinomial
            poly = PolynomialFeatures(degree=2, include_bias=False)
            X_poly = poly.fit_transform(X)
            
            # Regresión polinomial
            model = LinearRegression()
            model.fit(X_poly, y)
            y_pred = model.predict(X_poly)
            
            r_squared = r2_score(y, y_pred)
            mse = mean_squared_error(y, y_pred)
        else:
            r_squared = 0
            mse = 0
        
        # Validar supuestos
        assumptions_met = all(self.validate_assumptions(group) for group in load_groups)
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), eta_squared, self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(eta_squared, 'eta_squared')
        
        if p_value < self.config.alpha:
            conclusion = f"Existe diferencia significativa en escalabilidad entre escenarios (F={f_stat:.3f}, p={p_value:.4f})"
        else:
            conclusion = f"No se encontró diferencia significativa en escalabilidad entre escenarios (F={f_stat:.3f}, p={p_value:.4f})"
        
        if r_squared > 0.5:
            conclusion += f". Modelo de escalabilidad polinomial significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar rendimiento para cargas extremas",
            "Implementar escalado horizontal para sesiones concurrentes",
            "Optimizar algoritmos de grafos para grandes volúmenes"
        ]
        
        return ExperimentResult(
            experiment_name="System Scalability Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=eta_squared,
            confidence_interval=self.calculate_confidence_interval(df['overall_performance_score'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=assumptions_met,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_budget_distribution(self) -> ExperimentResult:
        """Analiza la distribución de presupuesto."""
        print("[PerformanceExperiment] Analizando distribución de presupuesto...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Análisis de distribución por rango de presupuesto
        budget_groups = [df[df['budget_range'] == budget]['distribution_efficiency'].values 
                        for budget in self.budget_ranges]
        
        # ANOVA para comparar eficiencia de distribución
        f_stat, p_value = f_oneway(*budget_groups)
        
        # Análisis de chi-cuadrado para distribución de porcentajes
        venue_percentages = df['venue_percentage'].values
        catering_percentages = df['catering_percentage'].values
        decor_percentages = df['decor_percentage'].values
        
        # Crear tabla de contingencia
        contingency_table = np.array([
            [np.mean(venue_percentages), np.mean(catering_percentages), np.mean(decor_percentages)],
            [np.std(venue_percentages), np.std(catering_percentages), np.std(decor_percentages)]
        ])
        
        chi2_stat, chi2_p_value, dof, expected = chi2_contingency(contingency_table)
        
        # Correlación entre eficiencia de distribución y satisfacción del usuario
        efficiency_satisfaction_corr, efficiency_satisfaction_p = pearsonr(
            df['distribution_efficiency'].values, df['user_satisfaction'].values
        )
        
        # Análisis de regresión para predecir satisfacción
        X = df[['distribution_efficiency', 'budget_total']].values
        y = df['user_satisfaction'].values
        
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
            f_stat_reg = results.fvalue
            f_p_value_reg = results.f_pvalue
        else:
            r_squared = 0
            f_stat_reg = 0
            f_p_value_reg = 1
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), abs(efficiency_satisfaction_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(efficiency_satisfaction_corr), 'cohens_d')
        
        conclusion = f"Análisis de distribución de presupuesto completado"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en eficiencia entre rangos (F={f_stat:.3f}, p={p_value:.4f})"
        
        if efficiency_satisfaction_p < self.config.alpha:
            conclusion += f". Correlación eficiencia-satisfacción: r={efficiency_satisfaction_corr:.3f} (p={efficiency_satisfaction_p:.4f})"
        
        if f_p_value_reg < self.config.alpha:
            conclusion += f". Modelo predictivo de satisfacción significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar algoritmos de distribución para presupuestos altos",
            "Implementar feedback de usuario para mejorar distribución",
            "Desarrollar modelos predictivos de satisfacción"
        ]
        
        return ExperimentResult(
            experiment_name="Budget Distribution Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(efficiency_satisfaction_corr),
            confidence_interval=self.calculate_confidence_interval(df['distribution_efficiency'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_resource_usage(self) -> ExperimentResult:
        """Analiza el uso de recursos del sistema."""
        print("[PerformanceExperiment] Analizando uso de recursos...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Análisis de correlación entre uso de recursos
        memory_cpu_corr, memory_cpu_p = pearsonr(
            df['memory_usage_mb'].values, df['cpu_usage_percent'].values
        )
        
        # Análisis de eficiencia de recursos por escenario
        resource_efficiency_groups = [df[df['load_scenario'] == scenario]['resource_efficiency'].values 
                                    for scenario in self.load_scenarios]
        
        # Test de Kruskal-Wallis (no paramétrico)
        h_stat, p_value = kruskal(*resource_efficiency_groups)
        
        # Análisis de regresión para predecir uso de memoria
        X = df[['concurrent_sessions', 'graph_size_nodes']].values
        y = df['memory_usage_mb'].values
        
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
            f_stat_reg = results.fvalue
            f_p_value_reg = results.f_pvalue
        else:
            r_squared = 0
            f_stat_reg = 0
            f_p_value_reg = 1
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), abs(memory_cpu_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(memory_cpu_corr), 'cohens_d')
        
        conclusion = f"Análisis de uso de recursos completado"
        
        if memory_cpu_p < self.config.alpha:
            conclusion += f". Correlación memoria-CPU: r={memory_cpu_corr:.3f} (p={memory_cpu_p:.4f})"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en eficiencia de recursos entre escenarios (H={h_stat:.3f}, p={p_value:.4f})"
        
        if f_p_value_reg < self.config.alpha:
            conclusion += f". Modelo predictivo de uso de memoria significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar uso de memoria para sesiones concurrentes",
            "Implementar gestión eficiente de recursos por escenario",
            "Desarrollar modelos predictivos de uso de recursos"
        ]
        
        return ExperimentResult(
            experiment_name="Resource Usage Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=h_stat,
            p_value=p_value,
            effect_size=abs(memory_cpu_corr),
            confidence_interval=self.calculate_confidence_interval(df['resource_efficiency'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,  # Kruskal-Wallis no requiere normalidad
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_throughput_performance(self) -> ExperimentResult:
        """Analiza el rendimiento de throughput del sistema."""
        print("[PerformanceExperiment] Analizando rendimiento de throughput...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Análisis de throughput por escenario de carga
        throughput_groups = [df[df['load_scenario'] == scenario]['throughput_ops_per_sec'].values 
                           for scenario in self.load_scenarios]
        
        # ANOVA para comparar throughput entre escenarios
        f_stat, p_value = f_oneway(*throughput_groups)
        
        # Correlación entre throughput y recursos
        throughput_memory_corr, throughput_memory_p = spearmanr(
            df['throughput_ops_per_sec'].values, df['memory_usage_mb'].values
        )
        
        throughput_cpu_corr, throughput_cpu_p = spearmanr(
            df['throughput_ops_per_sec'].values, df['cpu_usage_percent'].values
        )
        
        # Análisis de eficiencia de throughput
        throughput_efficiency = df['throughput_ops_per_sec'] / (df['memory_usage_mb'] + df['cpu_usage_percent'])
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), abs(throughput_memory_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(throughput_memory_corr), 'cohens_d')
        
        conclusion = f"Análisis de throughput completado"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en throughput entre escenarios (F={f_stat:.3f}, p={p_value:.4f})"
        
        if throughput_memory_p < self.config.alpha:
            conclusion += f". Correlación throughput-memoria: r={throughput_memory_corr:.3f} (p={throughput_memory_p:.4f})"
        
        recommendations = [
            "Optimizar throughput para cargas altas",
            "Balancear uso de recursos para maximizar throughput",
            "Implementar métricas de eficiencia de throughput"
        ]
        
        return ExperimentResult(
            experiment_name="Throughput Performance Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(throughput_memory_corr),
            confidence_interval=self.calculate_confidence_interval(df['throughput_ops_per_sec'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_latency_performance(self) -> ExperimentResult:
        """Analiza el rendimiento de latencia del sistema."""
        print("[PerformanceExperiment] Analizando rendimiento de latencia...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Análisis de latencia por escenario de carga
        latency_groups = [df[df['load_scenario'] == scenario]['response_time_ms'].values 
                         for scenario in self.load_scenarios]
        
        # Test de Kruskal-Wallis (no paramétrico para latencia)
        h_stat, p_value = kruskal(*latency_groups)
        
        # Correlación entre latencia y factores
        latency_sessions_corr, latency_sessions_p = spearmanr(
            df['response_time_ms'].values, df['concurrent_sessions'].values
        )
        
        latency_graph_corr, latency_graph_p = spearmanr(
            df['response_time_ms'].values, df['graph_size_nodes'].values
        )
        
        # Análisis de percentiles de latencia
        latency_percentiles = np.percentile(df['response_time_ms'].values, [50, 90, 95, 99])
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(df), abs(latency_sessions_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(latency_sessions_corr), 'cohens_d')
        
        conclusion = f"Análisis de latencia completado. P50: {latency_percentiles[0]:.1f}ms, P95: {latency_percentiles[2]:.1f}ms"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en latencia entre escenarios (H={h_stat:.3f}, p={p_value:.4f})"
        
        if latency_sessions_p < self.config.alpha:
            conclusion += f". Correlación latencia-sesiones: r={latency_sessions_corr:.3f} (p={latency_sessions_p:.4f})"
        
        recommendations = [
            "Optimizar latencia para sesiones concurrentes",
            "Implementar caching para reducir latencia",
            "Monitorear percentiles de latencia críticos"
        ]
        
        return ExperimentResult(
            experiment_name="Latency Performance Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(df),
            test_statistic=h_stat,
            p_value=p_value,
            effect_size=abs(latency_sessions_corr),
            confidence_interval=self.calculate_confidence_interval(df['response_time_ms'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,  # Kruskal-Wallis no requiere normalidad
            effect_significance=effect_significance,
            recommendations=recommendations
        )

def run_performance_experiments(system_components: Dict[str, Any]) -> List[ExperimentResult]:
    """Función principal para ejecutar todos los experimentos de rendimiento."""
    print("="*80)
    print("INICIANDO EXPERIMENTOS DE RENDIMIENTO DEL SISTEMA")
    print("="*80)
    
    # Configurar experimento
    config = ExperimentConfig(
        name="System_Performance_Complete",
        description="Análisis completo de rendimiento del sistema",
        alpha=0.05,
        power=0.8,
        effect_size=0.4,
        min_sample_size=30,
        max_sample_size=500
    )
    
    # Crear y ejecutar experimento con directorio de salida específico
    output_dir = os.path.join("results", "system_performance")
    experiment = SystemPerformanceExperiment(config, system_components, output_dir)
    results = experiment.run()
    
    # Generar visualizaciones
    experiment.generate_visualizations()
    
    # Guardar datos
    experiment.save_data()
    
    # Generar reporte
    data_summary = {
        'total_samples': len(experiment.data_buffer),
        'duration': f"{len(experiment.data_buffer)} operaciones simuladas",
        'experiments_completed': len(results)
    }
    
    report_file = experiment.reporter.generate_report(
        experiment.config.name, results, data_summary
    )
    
    print(f"\n✅ Experimentos de rendimiento completados:")
    print(f"   - Análisis realizados: {len(results)}")
    print(f"   - Operaciones procesadas: {len(experiment.data_buffer)}")
    print(f"   - Reporte generado: {report_file}")
    
    return results

if __name__ == "__main__":
    # Ejemplo de uso
    mock_components = {
        'planner': None,
        'memory': None,
        'bus': None
    }
    
    results = run_performance_experiments(mock_components)
    
    # Mostrar resumen de resultados
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS DE RENDIMIENTO")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.experiment_name}")
        print(f"   Conclusión: {result.conclusion}")
        print(f"   P-valor: {result.p_value:.4f}")
        print(f"   Tamaño del efecto: {result.effect_size:.3f} ({result.effect_significance})")
        print(f"   Potencia: {result.power_achieved:.3f}") 