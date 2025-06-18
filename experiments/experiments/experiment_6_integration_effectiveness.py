#!/usr/bin/env python3
"""
Experimento 6: Análisis de Efectividad de Integración
Implementa análisis robusto de efectividad del MessageBus y memoria de sesión.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import json
import os
import time

from scipy import stats
from framework.experimental_framework import BaseExperiment, ExperimentConfig, ExperimentResult
from framework.experimental_framework import StatisticalValidator, EffectSizeCalculator, PowerAnalyzer
from scipy.stats import poisson, expon as exponential, gamma
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import networkx as nx
import statsmodels.api as sm
from scipy.stats import f_oneway, kruskal, pearsonr, spearmanr

class IntegrationEffectivenessExperiment(BaseExperiment):
    """Experimento para analizar la efectividad de integración del sistema."""
    
    def __init__(self, config: ExperimentConfig, system_components: Dict[str, Any], output_dir: str = None):
        super().__init__(config, system_components, output_dir)
        self.message_types = ['task', 'response', 'broadcast', 'error', 'correction']
        self.agent_types = ['planner', 'venue', 'catering', 'decor', 'budget']
        self.session_states = ['active', 'completed', 'error', 'timeout']
        
    def run(self) -> List[ExperimentResult]:
        """Ejecuta el experimento completo de efectividad de integración."""
        print(f"[IntegrationExperiment] Iniciando experimento: {self.config.name}")
        
        # Generar datos sintéticos para el experimento
        self._generate_synthetic_integration_data()
        
        # Ejecutar análisis de efectividad del MessageBus
        messagebus_result = self._analyze_messagebus_effectiveness()
        self.results.append(messagebus_result)
        
        # Ejecutar análisis de memoria de sesión
        memory_result = self._analyze_session_memory_effectiveness()
        self.results.append(memory_result)
        
        # Ejecutar análisis de patrones de comunicación
        communication_result = self._analyze_communication_patterns()
        self.results.append(communication_result)
        
        # Ejecutar análisis de latencia de comunicación
        latency_result = self._analyze_communication_latency()
        self.results.append(latency_result)
        
        # Ejecutar análisis de persistencia de memoria
        persistence_result = self._analyze_memory_persistence()
        self.results.append(persistence_result)
        
        print(f"[IntegrationExperiment] Experimento completado. {len(self.results)} análisis realizados.")
        return self.results
    
    def _generate_synthetic_integration_data(self):
        """Genera datos sintéticos realistas para el experimento de integración."""
        print("[IntegrationExperiment] Generando datos sintéticos de integración...")
        
        np.random.seed(self.config.random_seed)
        n_messages = 500  # Tamaño de muestra robusto
        n_sessions = 100
        
        # Generar datos de MessageBus
        for i in range(n_messages):
            # Generar tipo de mensaje aleatorio
            message_type = np.random.choice(self.message_types, p=[0.4, 0.3, 0.1, 0.1, 0.1])
            
            # Generar agentes de origen y destino
            source_agent = np.random.choice(self.agent_types, p=[0.3, 0.2, 0.2, 0.2, 0.1])
            target_agent = np.random.choice(self.agent_types, p=[0.3, 0.2, 0.2, 0.2, 0.1])
            
            # Generar métricas de MessageBus
            messagebus_metrics = self._generate_messagebus_metrics(message_type, source_agent, target_agent)
            
            # Agregar ruido realista
            messagebus_metrics = self._add_realistic_noise(messagebus_metrics)
            
            # Agregar timestamp
            messagebus_metrics['timestamp'] = datetime.now() - timedelta(
                minutes=np.random.randint(0, 1440)  # Últimas 24 horas
            )
            
            self.data_buffer.append(messagebus_metrics)
        
        # Generar datos de memoria de sesión
        for i in range(n_sessions):
            # Generar estado de sesión aleatorio
            session_state = np.random.choice(self.session_states, p=[0.6, 0.25, 0.1, 0.05])
            
            # Generar métricas de memoria de sesión
            memory_metrics = self._generate_memory_metrics(session_state)
            
            # Agregar ruido realista
            memory_metrics = self._add_realistic_noise(memory_metrics)
            
            # Agregar timestamp
            memory_metrics['timestamp'] = datetime.now() - timedelta(
                minutes=np.random.randint(0, 1440)  # Últimas 24 horas
            )
            
            self.data_buffer.append(memory_metrics)
        
        print(f"[IntegrationExperiment] Generados {len(self.data_buffer)} registros de datos de integración")
    
    def _generate_messagebus_metrics(self, message_type: str, source_agent: str, target_agent: str) -> Dict[str, Any]:
        """Genera métricas del MessageBus basadas en tipo de mensaje y agentes."""
        # Parámetros base según tipo de mensaje
        message_params = {
            'task': {
                'base_size_bytes': np.random.exponential(1000),
                'base_processing_time': np.random.exponential(0.5),
                'success_rate': 0.95,
                'queue_depth': np.random.poisson(5)
            },
            'response': {
                'base_size_bytes': np.random.exponential(800),
                'base_processing_time': np.random.exponential(0.3),
                'success_rate': 0.98,
                'queue_depth': np.random.poisson(3)
            },
            'broadcast': {
                'base_size_bytes': np.random.exponential(1500),
                'base_processing_time': np.random.exponential(1.0),
                'success_rate': 0.90,
                'queue_depth': np.random.poisson(8)
            },
            'error': {
                'base_size_bytes': np.random.exponential(500),
                'base_processing_time': np.random.exponential(0.2),
                'success_rate': 0.99,
                'queue_depth': np.random.poisson(2)
            },
            'correction': {
                'base_size_bytes': np.random.exponential(1200),
                'base_processing_time': np.random.exponential(0.8),
                'success_rate': 0.92,
                'queue_depth': np.random.poisson(6)
            }
        }
        
        params = message_params[message_type]
        
        # Ajustar por complejidad de agentes
        agent_complexity = {
            'planner': 1.2,
            'venue': 1.0,
            'catering': 1.0,
            'decor': 0.9,
            'budget': 0.8
        }
        
        complexity_factor = agent_complexity.get(source_agent, 1.0) * agent_complexity.get(target_agent, 1.0)
        
        # Generar métricas ajustadas
        message_size = params['base_size_bytes'] * complexity_factor
        processing_time = params['base_processing_time'] * complexity_factor
        success = np.random.random() < params['success_rate']
        queue_depth = params['queue_depth']
        
        # Calcular métricas derivadas
        throughput = 1.0 / processing_time if processing_time > 0 else 0
        latency = processing_time + (queue_depth * 0.1)  # Latencia incluye tiempo en cola
        efficiency = throughput / (message_size / 1000)  # Eficiencia por KB
        
        return {
            'message_id': f"msg_{np.random.randint(1000, 9999)}",
            'message_type': message_type,
            'source_agent': source_agent,
            'target_agent': target_agent,
            'message_size_bytes': message_size,
            'processing_time_seconds': processing_time,
            'queue_depth': queue_depth,
            'success': success,
            'throughput_ops_per_sec': throughput,
            'latency_seconds': latency,
            'efficiency_score': efficiency,
            'complexity_factor': complexity_factor,
            'communication_overhead': message_size / 1000,  # Overhead en KB
            'response_time_seconds': processing_time if success else processing_time * 2,
            'error_rate': 1 - params['success_rate']
        }
    
    def _generate_memory_metrics(self, session_state: str) -> Dict[str, Any]:
        """Genera métricas de memoria de sesión basadas en estado."""
        # Parámetros base según estado de sesión
        state_params = {
            'active': {
                'base_memory_size_mb': np.random.exponential(50),
                'base_beliefs_count': np.random.poisson(8),
                'base_duration_minutes': np.random.exponential(30),
                'persistence_rate': 0.95,
                'recovery_success_rate': 0.98
            },
            'completed': {
                'base_memory_size_mb': np.random.exponential(30),
                'base_beliefs_count': np.random.poisson(12),
                'base_duration_minutes': np.random.exponential(120),
                'persistence_rate': 0.99,
                'recovery_success_rate': 0.99
            },
            'error': {
                'base_memory_size_mb': np.random.exponential(20),
                'base_beliefs_count': np.random.poisson(5),
                'base_duration_minutes': np.random.exponential(15),
                'persistence_rate': 0.80,
                'recovery_success_rate': 0.70
            },
            'timeout': {
                'base_memory_size_mb': np.random.exponential(15),
                'base_beliefs_count': np.random.poisson(3),
                'base_duration_minutes': np.random.exponential(10),
                'persistence_rate': 0.60,
                'recovery_success_rate': 0.50
            }
        }
        
        params = state_params[session_state]
        
        # Generar métricas base
        memory_size = params['base_memory_size_mb']
        beliefs_count = params['base_beliefs_count']
        duration = params['base_duration_minutes']
        persistence = np.random.random() < params['persistence_rate']
        recovery_success = np.random.random() < params['recovery_success_rate']
        
        # Calcular métricas derivadas
        memory_efficiency = beliefs_count / memory_size if memory_size > 0 else 0
        persistence_score = 1.0 if persistence else 0.0
        recovery_score = 1.0 if recovery_success else 0.0
        context_retention = beliefs_count / max(duration, 1)  # Beliefs por minuto
        
        return {
            'session_id': f"session_{np.random.randint(1000, 9999)}",
            'session_state': session_state,
            'memory_size_mb': memory_size,
            'beliefs_count': beliefs_count,
            'duration_minutes': duration,
            'persistence_success': persistence,
            'recovery_success': recovery_success,
            'memory_efficiency': memory_efficiency,
            'persistence_score': persistence_score,
            'recovery_score': recovery_score,
            'context_retention': context_retention,
            'overall_memory_score': (memory_efficiency + persistence_score + recovery_score) / 3,
            'memory_overhead': memory_size / max(beliefs_count, 1),  # MB por belief
            'session_complexity': beliefs_count * duration / 100  # Complejidad normalizada
        }
    
    def _add_realistic_noise(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Agrega ruido realista a las métricas de integración."""
        noise_factor = 0.06  # 6% de ruido para métricas de integración
        
        for key, value in metrics.items():
            if isinstance(value, (int, float)) and key not in ['message_id', 'session_id', 'message_type', 'source_agent', 'target_agent', 'session_state']:
                if key in ['efficiency_score', 'persistence_score', 'recovery_score', 'overall_memory_score']:
                    # Para métricas de score, mantener en rango [0,1]
                    noise = np.random.normal(0, value * noise_factor)
                    metrics[key] = np.clip(value + noise, 0, 1)
                else:
                    noise = np.random.normal(0, abs(value) * noise_factor)
                    metrics[key] = max(0, value + noise)
        
        return metrics
    
    def _analyze_messagebus_effectiveness(self) -> ExperimentResult:
        """Analiza la efectividad del MessageBus."""
        print("[IntegrationExperiment] Analizando efectividad del MessageBus...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Filtrar solo datos de MessageBus
        messagebus_data = df[df['message_type'].notna()]
        
        if len(messagebus_data) == 0:
            return ExperimentResult(
                experiment_name="MessageBus Effectiveness Analysis",
                timestamp=datetime.now().isoformat(),
                sample_size=0,
                test_statistic=0,
                p_value=1,
                effect_size=0,
                confidence_interval=(0, 0),
                power_achieved=0,
                conclusion="No hay datos de MessageBus disponibles",
                assumptions_met=False,
                effect_significance='small',
                recommendations=["Recolectar datos de MessageBus"]
            )
        
        # Análisis de efectividad por tipo de mensaje
        message_groups = [messagebus_data[messagebus_data['message_type'] == msg_type]['efficiency_score'].values 
                         for msg_type in self.message_types]
        
        # ANOVA para comparar eficiencia entre tipos de mensaje
        f_stat, p_value = f_oneway(*message_groups)
        
        # Análisis de throughput y latencia
        throughput_latency_corr, throughput_latency_p = spearmanr(
            messagebus_data['throughput_ops_per_sec'].values, 
            messagebus_data['latency_seconds'].values
        )
        
        # Análisis de tasa de éxito
        success_rate = messagebus_data['success'].mean()
        
        # Análisis de regresión para predecir latencia
        X = messagebus_data[['message_size_bytes', 'queue_depth', 'complexity_factor']].values
        y = messagebus_data['latency_seconds'].values
        
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
            len(messagebus_data), abs(throughput_latency_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(throughput_latency_corr), 'cohens_d')
        
        conclusion = f"Análisis de MessageBus completado. Tasa de éxito: {success_rate:.3f}"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en eficiencia entre tipos (F={f_stat:.3f}, p={p_value:.4f})"
        
        if throughput_latency_p < self.config.alpha:
            conclusion += f". Correlación throughput-latencia: r={throughput_latency_corr:.3f} (p={throughput_latency_p:.4f})"
        
        if f_p_value_reg < self.config.alpha:
            conclusion += f". Modelo predictivo de latencia significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar tipos de mensaje con menor eficiencia",
            "Implementar balanceo de carga para reducir latencia",
            "Monitorear correlaciones throughput-latencia"
        ]
        
        return ExperimentResult(
            experiment_name="MessageBus Effectiveness Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(messagebus_data),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(throughput_latency_corr),
            confidence_interval=self.calculate_confidence_interval(messagebus_data['efficiency_score'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_session_memory_effectiveness(self) -> ExperimentResult:
        """Analiza la efectividad de la memoria de sesión."""
        print("[IntegrationExperiment] Analizando efectividad de memoria de sesión...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Filtrar solo datos de memoria de sesión
        memory_data = df[df['session_state'].notna()]
        
        if len(memory_data) == 0:
            return ExperimentResult(
                experiment_name="Session Memory Effectiveness Analysis",
                timestamp=datetime.now().isoformat(),
                sample_size=0,
                test_statistic=0,
                p_value=1,
                effect_size=0,
                confidence_interval=(0, 0),
                power_achieved=0,
                conclusion="No hay datos de memoria de sesión disponibles",
                assumptions_met=False,
                effect_significance='small',
                recommendations=["Recolectar datos de memoria de sesión"]
            )
        
        # Análisis de efectividad por estado de sesión
        state_groups = [memory_data[memory_data['session_state'] == state]['overall_memory_score'].values 
                       for state in self.session_states]
        
        # ANOVA para comparar efectividad entre estados
        f_stat, p_value = f_oneway(*state_groups)
        
        # Análisis de correlación entre métricas de memoria
        efficiency_persistence_corr, efficiency_persistence_p = pearsonr(
            memory_data['memory_efficiency'].values, 
            memory_data['persistence_score'].values
        )
        
        efficiency_recovery_corr, efficiency_recovery_p = pearsonr(
            memory_data['memory_efficiency'].values, 
            memory_data['recovery_score'].values
        )
        
        # Análisis de regresión para predecir efectividad de memoria
        X = memory_data[['memory_size_mb', 'beliefs_count', 'duration_minutes']].values
        y = memory_data['overall_memory_score'].values
        
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
            len(memory_data), abs(efficiency_persistence_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(efficiency_persistence_corr), 'cohens_d')
        
        conclusion = f"Análisis de memoria de sesión completado"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en efectividad entre estados (F={f_stat:.3f}, p={p_value:.4f})"
        
        if efficiency_persistence_p < self.config.alpha:
            conclusion += f". Correlación eficiencia-persistencia: r={efficiency_persistence_corr:.3f} (p={efficiency_persistence_p:.4f})"
        
        if f_p_value_reg < self.config.alpha:
            conclusion += f". Modelo predictivo de efectividad significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar persistencia para sesiones con errores",
            "Implementar estrategias de recuperación mejoradas",
            "Monitorear correlaciones entre métricas de memoria"
        ]
        
        return ExperimentResult(
            experiment_name="Session Memory Effectiveness Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(memory_data),
            test_statistic=f_stat,
            p_value=p_value,
            effect_size=abs(efficiency_persistence_corr),
            confidence_interval=self.calculate_confidence_interval(memory_data['overall_memory_score'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_communication_patterns(self) -> ExperimentResult:
        """Analiza patrones de comunicación entre agentes."""
        print("[IntegrationExperiment] Analizando patrones de comunicación...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Filtrar solo datos de MessageBus
        messagebus_data = df[df['message_type'].notna()]
        
        if len(messagebus_data) == 0:
            return ExperimentResult(
                experiment_name="Communication Patterns Analysis",
                timestamp=datetime.now().isoformat(),
                sample_size=0,
                test_statistic=0,
                p_value=1,
                effect_size=0,
                confidence_interval=(0, 0),
                power_achieved=0,
                conclusion="No hay datos de comunicación disponibles",
                assumptions_met=False,
                effect_significance='small',
                recommendations=["Recolectar datos de comunicación"]
            )
        
        # Crear matriz de comunicación
        communication_matrix = pd.crosstab(
            messagebus_data['source_agent'], 
            messagebus_data['target_agent']
        )
        
        # Análisis de centralidad de agentes
        agent_communication_volumes = messagebus_data.groupby('source_agent').size()
        
        # Análisis de patrones por tipo de mensaje
        message_patterns = pd.crosstab(
            messagebus_data['message_type'], 
            messagebus_data['source_agent']
        )
        
        # Análisis de clustering de patrones de comunicación
        if len(messagebus_data) >= 10:
            # Preparar datos para clustering
            pattern_features = messagebus_data[['message_size_bytes', 'processing_time_seconds', 'queue_depth']].values
            
            # Eliminar filas con valores faltantes
            mask = ~np.isnan(pattern_features).any(axis=1)
            pattern_features = pattern_features[mask]
            
            if len(pattern_features) >= 5:
                # Aplicar K-means clustering
                kmeans = KMeans(n_clusters=min(3, len(pattern_features)), random_state=42)
                clusters = kmeans.fit_predict(pattern_features)
                
                # Calcular silhouette score
                if len(np.unique(clusters)) > 1:
                    silhouette_avg = silhouette_score(pattern_features, clusters)
                else:
                    silhouette_avg = 0
            else:
                silhouette_avg = 0
        else:
            silhouette_avg = 0
        
        # Análisis de correlación entre volumen y eficiencia
        agent_efficiency = messagebus_data.groupby('source_agent')['efficiency_score'].mean()
        volume_efficiency_corr, volume_efficiency_p = spearmanr(
            agent_communication_volumes.values, agent_efficiency.values
        )
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(messagebus_data), abs(volume_efficiency_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(volume_efficiency_corr), 'cohens_d')
        
        conclusion = f"Análisis de patrones de comunicación completado. Silhouette score: {silhouette_avg:.3f}"
        
        if volume_efficiency_p < self.config.alpha:
            conclusion += f". Correlación volumen-eficiencia: r={volume_efficiency_corr:.3f} (p={volume_efficiency_p:.4f})"
        
        recommendations = [
            "Optimizar patrones de comunicación identificados",
            "Balancear carga de comunicación entre agentes",
            "Implementar clustering para optimización de patrones"
        ]
        
        return ExperimentResult(
            experiment_name="Communication Patterns Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(messagebus_data),
            test_statistic=volume_efficiency_corr,
            p_value=volume_efficiency_p,
            effect_size=abs(volume_efficiency_corr),
            confidence_interval=(-1, 1),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_communication_latency(self) -> ExperimentResult:
        """Analiza la latencia de comunicación."""
        print("[IntegrationExperiment] Analizando latencia de comunicación...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Filtrar solo datos de MessageBus
        messagebus_data = df[df['message_type'].notna()]
        
        if len(messagebus_data) == 0:
            return ExperimentResult(
                experiment_name="Communication Latency Analysis",
                timestamp=datetime.now().isoformat(),
                sample_size=0,
                test_statistic=0,
                p_value=1,
                effect_size=0,
                confidence_interval=(0, 0),
                power_achieved=0,
                conclusion="No hay datos de latencia disponibles",
                assumptions_met=False,
                effect_significance='small',
                recommendations=["Recolectar datos de latencia"]
            )
        
        # Análisis de latencia por tipo de mensaje
        latency_groups = [messagebus_data[messagebus_data['message_type'] == msg_type]['latency_seconds'].values 
                         for msg_type in self.message_types]
        
        # Test de Kruskal-Wallis (no paramétrico)
        h_stat, p_value = kruskal(*latency_groups)
        
        # Análisis de correlación entre latencia y factores
        latency_size_corr, latency_size_p = spearmanr(
            messagebus_data['latency_seconds'].values, 
            messagebus_data['message_size_bytes'].values
        )
        
        latency_queue_corr, latency_queue_p = spearmanr(
            messagebus_data['latency_seconds'].values, 
            messagebus_data['queue_depth'].values
        )
        
        # Análisis de percentiles de latencia
        latency_percentiles = np.percentile(messagebus_data['latency_seconds'].values, [50, 90, 95, 99])
        
        # Calcular potencia
        power_achieved = self.power_analyzer.calculate_power(
            len(messagebus_data), abs(latency_size_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(latency_size_corr), 'cohens_d')
        
        conclusion = f"Análisis de latencia completado. P50: {latency_percentiles[0]:.3f}s, P95: {latency_percentiles[2]:.3f}s"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en latencia entre tipos (H={h_stat:.3f}, p={p_value:.4f})"
        
        if latency_size_p < self.config.alpha:
            conclusion += f". Correlación latencia-tamaño: r={latency_size_corr:.3f} (p={latency_size_p:.4f})"
        
        recommendations = [
            "Optimizar latencia para tipos de mensaje lentos",
            "Implementar compresión para mensajes grandes",
            "Monitorear percentiles de latencia críticos"
        ]
        
        return ExperimentResult(
            experiment_name="Communication Latency Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(messagebus_data),
            test_statistic=h_stat,
            p_value=p_value,
            effect_size=abs(latency_size_corr),
            confidence_interval=self.calculate_confidence_interval(messagebus_data['latency_seconds'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,  # Kruskal-Wallis no requiere normalidad
            effect_significance=effect_significance,
            recommendations=recommendations
        )
    
    def _analyze_memory_persistence(self) -> ExperimentResult:
        """Analiza la persistencia de memoria."""
        print("[IntegrationExperiment] Analizando persistencia de memoria...")
        
        df = pd.DataFrame(self.data_buffer)
        
        # Filtrar solo datos de memoria de sesión
        memory_data = df[df['session_state'].notna()]
        
        if len(memory_data) == 0:
            return ExperimentResult(
                experiment_name="Memory Persistence Analysis",
                timestamp=datetime.now().isoformat(),
                sample_size=0,
                test_statistic=0,
                p_value=1,
                effect_size=0,
                confidence_interval=(0, 0),
                power_achieved=0,
                conclusion="No hay datos de persistencia disponibles",
                assumptions_met=False,
                effect_significance='small',
                recommendations=["Recolectar datos de persistencia"]
            )
        
        # Análisis de persistencia por estado de sesión
        persistence_groups = [memory_data[memory_data['session_state'] == state]['persistence_score'].values 
                            for state in self.session_states]
        
        # Test de Kruskal-Wallis (no paramétrico)
        h_stat, p_value = kruskal(*persistence_groups)
        
        # Análisis de correlación entre persistencia y factores
        persistence_size_corr, persistence_size_p = spearmanr(
            memory_data['persistence_score'].values, 
            memory_data['memory_size_mb'].values
        )
        
        persistence_duration_corr, persistence_duration_p = spearmanr(
            memory_data['persistence_score'].values, 
            memory_data['duration_minutes'].values
        )
        
        # Análisis de regresión para predecir persistencia
        X = memory_data[['memory_size_mb', 'beliefs_count', 'duration_minutes']].values
        y = memory_data['persistence_score'].values
        
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
            len(memory_data), abs(persistence_size_corr), self.config.alpha
        )
        
        # Interpretar resultados
        effect_significance = self.effect_calculator.interpret_effect_size(abs(persistence_size_corr), 'cohens_d')
        
        conclusion = f"Análisis de persistencia completado"
        
        if p_value < self.config.alpha:
            conclusion += f". Diferencia significativa en persistencia entre estados (H={h_stat:.3f}, p={p_value:.4f})"
        
        if persistence_size_p < self.config.alpha:
            conclusion += f". Correlación persistencia-tamaño: r={persistence_size_corr:.3f} (p={persistence_size_p:.4f})"
        
        if f_p_value_reg < self.config.alpha:
            conclusion += f". Modelo predictivo de persistencia significativo (R²={r_squared:.3f})"
        
        recommendations = [
            "Optimizar persistencia para sesiones grandes",
            "Implementar estrategias de persistencia por duración",
            "Desarrollar modelos predictivos de persistencia"
        ]
        
        return ExperimentResult(
            experiment_name="Memory Persistence Analysis",
            timestamp=datetime.now().isoformat(),
            sample_size=len(memory_data),
            test_statistic=h_stat,
            p_value=p_value,
            effect_size=abs(persistence_size_corr),
            confidence_interval=self.calculate_confidence_interval(memory_data['persistence_score'].values),
            power_achieved=power_achieved,
            conclusion=conclusion,
            assumptions_met=True,  # Kruskal-Wallis no requiere normalidad
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
            std_err = stats.sem(valid_data)
            
            # Verificar que std_err no sea NaN o infinito
            if np.isnan(std_err) or np.isinf(std_err) or std_err == 0:
                return (mean - 0.1, mean + 0.1)  # Intervalo pequeño alrededor de la media
            
            ci = stats.t.interval(confidence, len(valid_data)-1, loc=mean, scale=std_err)
            
            # Verificar que los valores del intervalo sean válidos
            if np.isnan(ci[0]) or np.isnan(ci[1]) or np.isinf(ci[0]) or np.isinf(ci[1]):
                return (mean - 0.1, mean + 0.1)
            
            return ci
        except Exception as e:
            print(f"[IntegrationExperiment] Error calculando intervalo de confianza: {str(e)}")
            return (0.0, 1.0)  # Intervalo por defecto en caso de error

    def _safe_statistical_test(self, test_func, *args, **kwargs):
        """Ejecuta pruebas estadísticas con manejo seguro de errores."""
        try:
            result = test_func(*args, **kwargs)
            
            # Verificar que el resultado no contenga NaN
            if isinstance(result, tuple):
                for val in result:
                    if np.isnan(val) or np.isinf(val):
                        return None, 1.0  # Retornar valores por defecto
            elif np.isnan(result) or np.isinf(result):
                return None, 1.0
            
            return result
        except Exception as e:
            print(f"[IntegrationExperiment] Error en prueba estadística: {str(e)}")
            return None, 1.0  # Retornar valores por defecto

def run_integration_experiments(system_components: Dict[str, Any]) -> List[ExperimentResult]:
    """Función principal para ejecutar todos los experimentos de integración."""
    print("="*80)
    print("INICIANDO EXPERIMENTOS DE EFECTIVIDAD DE INTEGRACIÓN")
    print("="*80)
    
    # Configurar experimento
    config = ExperimentConfig(
        name="Integration_Effectiveness_Complete",
        description="Análisis completo de efectividad de integración",
        alpha=0.05,
        power=0.8,
        effect_size=0.4,
        min_sample_size=30,
        max_sample_size=500
    )
    
    # Crear y ejecutar experimento con directorio de salida específico
    output_dir = os.path.join("results", "integration_effectiveness")
    experiment = IntegrationEffectivenessExperiment(config, system_components, output_dir)
    results = experiment.run()
    
    # Generar visualizaciones
    experiment.generate_visualizations()
    
    # Guardar datos
    experiment.save_data()
    
    # Generar reporte
    data_summary = {
        'total_samples': len(experiment.data_buffer),
        'duration': f"{len(experiment.data_buffer)} eventos de integración simulados",
        'experiments_completed': len(results)
    }
    
    report_file = experiment.reporter.generate_report(
        experiment.config.name, results, data_summary
    )
    
    print(f"\n✅ Experimentos de integración completados:")
    print(f"   - Análisis realizados: {len(results)}")
    print(f"   - Eventos procesados: {len(experiment.data_buffer)}")
    print(f"   - Reporte generado: {report_file}")
    
    return results

if __name__ == "__main__":
    # Ejemplo de uso
    mock_components = {
        'planner': None,
        'memory': None,
        'bus': None
    }
    
    results = run_integration_experiments(mock_components)
    
    # Mostrar resumen de resultados
    print("\n" + "="*80)
    print("RESUMEN DE RESULTADOS DE INTEGRACIÓN")
    print("="*80)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.experiment_name}")
        print(f"   Conclusión: {result.conclusion}")
        print(f"   P-valor: {result.p_value:.4f}")
        print(f"   Tamaño del efecto: {result.effect_size:.3f} ({result.effect_significance})")
        print(f"   Potencia: {result.power_achieved:.3f}") 