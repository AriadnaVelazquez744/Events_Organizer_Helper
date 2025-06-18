#!/usr/bin/env python3
"""
Script Principal para Ejecutar Todos los Experimentos Estadísticos
Ejecuta los experimentos 2, 3, 5 y 6 con metodología robusta y validación estadística completa.
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Importar experimentos
from experiments.experiment_2_bdi_effectiveness import run_bdi_experiments
from experiments.experiment_3_rag_precision import run_rag_experiments
from experiments.experiment_5_system_performance import run_performance_experiments
from experiments.experiment_6_integration_effectiveness import run_integration_experiments

class ExperimentRunner:
    """Ejecutor principal de todos los experimentos."""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        self.results_summary = {}
        self.execution_times = {}
        self.overall_stats = {}
        
        # Crear directorio de resultados
        Path(output_dir).mkdir(exist_ok=True)
        
        # Configurar estilo de gráficos
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
    
    def run_all_experiments(self, system_components: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta todos los experimentos y genera reporte consolidado."""
        print("="*100)
        print("EJECUTANDO SUITE COMPLETA DE EXPERIMENTOS ESTADÍSTICOS")
        print("="*100)
        print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*100)
        
        if system_components is None:
            system_components = self._create_mock_components()
        
        # Ejecutar experimentos
        experiments = {
            "BDI_Effectiveness": run_bdi_experiments,
            "RAG_Precision": run_rag_experiments,
            "System_Performance": run_performance_experiments,
            "Integration_Effectiveness": run_integration_experiments
        }
        
        all_results = {}
        
        for exp_name, exp_function in experiments.items():
            print(f"\n{'='*20} EJECUTANDO {exp_name} {'='*20}")
            start_time = time.time()
            
            try:
                results = exp_function(system_components)
                execution_time = time.time() - start_time
                
                all_results[exp_name] = {
                    'results': results,
                    'execution_time': execution_time,
                    'status': 'completed',
                    'timestamp': datetime.now().isoformat()
                }
                
                self.execution_times[exp_name] = execution_time
                
                print(f"✅ {exp_name} completado en {execution_time:.2f} segundos")
                print(f"   - Análisis realizados: {len(results)}")
                print(f"   - Resultados significativos: {sum(1 for r in results if r.p_value < 0.05)}")
                
            except Exception as e:
                execution_time = time.time() - start_time
                all_results[exp_name] = {
                    'results': [],
                    'execution_time': execution_time,
                    'status': 'failed',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"❌ {exp_name} falló después de {execution_time:.2f} segundos")
                print(f"   Error: {str(e)}")
        
        # Generar análisis consolidado
        self._generate_consolidated_analysis(all_results)
        
        # Generar reporte final
        self._generate_final_report(all_results)
        
        # Generar visualizaciones consolidadas
        self._generate_consolidated_visualizations(all_results)
        
        print(f"\n{'='*100}")
        print("SUITE DE EXPERIMENTOS COMPLETADA")
        print(f"Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Tiempo total: {sum(self.execution_times.values()):.2f} segundos")
        print(f"Resultados guardados en: {self.output_dir}")
        print("="*100)
        
        return all_results
    
    def _create_mock_components(self) -> Dict[str, Any]:
        """Crea componentes mock para experimentos."""
        return {
            'planner': None,
            'memory': None,
            'bus': None,
            'venue_rag': None,
            'catering_rag': None,
            'decor_rag': None
        }
    
    def _serialize_data_for_json(self, data):
        """Serializa datos para JSON, manejando tipos especiales."""
        if isinstance(data, pd.DataFrame):
            return data.to_dict('records')
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (datetime, pd.Timestamp)):
            return data.isoformat()
        elif isinstance(data, np.bool_):
            return bool(data)
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, dict):
            return {k: self._serialize_data_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_data_for_json(item) for item in data]
        else:
            return data

    def _generate_consolidated_analysis(self, all_results: Dict[str, Any]):
        """Genera análisis consolidado de todos los experimentos."""
        print("\n📊 Generando análisis consolidado...")
        
        # Preparar datos para análisis consolidado
        consolidated_data = {
            'experiment_summary': {},
            'statistical_summary': {},
            'performance_metrics': {},
            'recommendations': [],
            'timestamp': datetime.now().isoformat()
        }
        
        total_analyses = 0
        significant_analyses = 0
        total_power = 0
        total_effect_size = 0
        
        for exp_name, exp_data in all_results.items():
            if exp_data['status'] == 'completed':
                results = exp_data['results']
                total_analyses += len(results)
                
                # Contar análisis significativos
                exp_significant = sum(1 for r in results if r.p_value < 0.05)
                significant_analyses += exp_significant
                
                # Calcular métricas promedio
                if results:
                    avg_power = np.mean([r.power_achieved for r in results])
                    avg_effect_size = np.mean([r.effect_size for r in results])
                    total_power += avg_power
                    total_effect_size += avg_effect_size
                
                # Resumen por experimento
                consolidated_data['experiment_summary'][exp_name] = {
                    'total_analyses': len(results),
                    'significant_analyses': exp_significant,
                    'significance_rate': exp_significant / len(results) if results else 0,
                    'avg_power': avg_power if results else 0,
                    'avg_effect_size': avg_effect_size if results else 0,
                    'execution_time': self.execution_times.get(exp_name, 0)
                }
        
        # Métricas globales
        if total_analyses > 0:
            consolidated_data['statistical_summary'] = {
                'total_experiments': len([exp for exp in all_results.values() if exp['status'] == 'completed']),
                'total_analyses': total_analyses,
                'significant_analyses': significant_analyses,
                'overall_significance_rate': significant_analyses / total_analyses,
                'avg_power': total_power / len([exp for exp in all_results.values() if exp['status'] == 'completed']),
                'avg_effect_size': total_effect_size / len([exp for exp in all_results.values() if exp['status'] == 'completed'])
            }
        
        # Serializar datos para JSON
        serialized_data = self._serialize_data_for_json(consolidated_data)
        
        # Guardar análisis consolidado
        consolidated_file = os.path.join(self.output_dir, "consolidated_analysis.json")
        with open(consolidated_file, 'w', encoding='utf-8') as f:
            json.dump(serialized_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Análisis consolidado guardado en: {consolidated_file}")
        
        # Actualizar estadísticas globales
        self.overall_stats.update({
            'total_experiments': len(all_results),
            'completed_experiments': len([exp for exp in all_results.values() if exp['status'] == 'completed']),
            'total_analyses': total_analyses,
            'significant_analyses': significant_analyses,
            'average_power': total_power / len([exp for exp in all_results.values() if exp['status'] == 'completed']) if total_analyses > 0 else 0,
            'average_effect_size': total_effect_size / len([exp for exp in all_results.values() if exp['status'] == 'completed']) if total_analyses > 0 else 0,
            'total_execution_time': sum(self.execution_times.values())
        })
    
    def _generate_final_report(self, all_results: Dict[str, Any]):
        """Genera reporte final consolidado."""
        print("\n📋 Generando reporte final...")
        
        # Crear DataFrame para análisis
        report_data = []
        
        for exp_name, exp_data in all_results.items():
            if exp_data['status'] == 'completed':
                for result in exp_data['results']:
                    report_data.append({
                        'Experimento': exp_name,
                        'Análisis': result.experiment_name,
                        'P-Valor': result.p_value,
                        'Tamaño_Efecto': result.effect_size,
                        'Significancia_Efecto': result.effect_significance,
                        'Potencia': result.power_achieved,
                        'Tamaño_Muestra': result.sample_size,
                        'Significativo': 'Sí' if result.p_value < 0.05 else 'No',
                        'Supuestos_Cumplidos': 'Sí' if result.assumptions_met else 'No'
                    })
        
        df = pd.DataFrame(report_data)
        
        # Generar reporte HTML
        html_content = self._create_html_report(df, all_results)
        
        report_file = os.path.join(self.output_dir, "reporte_final_experimentos.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Generar reporte CSV solo si hay datos
        if not df.empty:
            csv_file = os.path.join(self.output_dir, "resultados_detallados.csv")
            df.to_csv(csv_file, index=False, encoding='utf-8')
            print(f"✅ Datos detallados guardados en: {csv_file}")
        
        print(f"✅ Reporte final guardado en: {report_file}")
    
    def _create_html_report(self, df: pd.DataFrame, all_results: Dict[str, Any]) -> str:
        """Crea el contenido HTML del reporte final."""
        
        # Verificar si el DataFrame está vacío
        if df.empty:
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Reporte Final - Suite de Experimentos Estadísticos</title>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                    .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; }}
                    .error {{ background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📊 Reporte Final - Suite de Experimentos Estadísticos</h1>
                        <p>Análisis completo de efectividad del sistema de planificación de eventos</p>
                        <p>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="error">
                        <h2>⚠️ No se encontraron resultados válidos</h2>
                        <p>Los experimentos no pudieron completarse debido a errores en la ejecución.</p>
                        <p>Por favor, revise los logs de error y corrija los problemas antes de volver a ejecutar.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            return html
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reporte Final - Suite de Experimentos Estadísticos</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 8px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
                .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }}
                .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
                .section {{ margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }}
                .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #667eea; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .significant {{ background-color: #d4edda; }}
                .not-significant {{ background-color: #f8d7da; }}
                .summary {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .recommendations {{ background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .recommendations h3 {{ color: #1976d2; }}
                .recommendations ul {{ margin: 10px 0; }}
                .recommendations li {{ margin: 5px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Reporte Final - Suite de Experimentos Estadísticos</h1>
                    <p>Análisis completo de efectividad del sistema de planificación de eventos</p>
                    <p>Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary">
                    <h2>📈 Resumen Ejecutivo</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Experimentos Completados</div>
                            <div class="stat-number">{self.overall_stats.get('completed_experiments', 0)}/{self.overall_stats.get('total_experiments', 0)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Análisis Totales</div>
                            <div class="stat-number">{self.overall_stats.get('total_analyses', 0)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Análisis Significativos</div>
                            <div class="stat-number">{self.overall_stats.get('significant_analyses', 0)}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Tasa de Significancia</div>
                            <div class="stat-number">{(self.overall_stats.get('significant_analyses', 0) / self.overall_stats.get('total_analyses', 1) * 100):.1f}%</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Potencia Promedio</div>
                            <div class="stat-number">{self.overall_stats.get('average_power', 0):.3f}</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Tamaño de Efecto Promedio</div>
                            <div class="stat-number">{self.overall_stats.get('average_effect_size', 0):.3f}</div>
                        </div>
                    </div>
                </div>
                
                <div class="section">
                    <h2>🔬 Resultados Detallados por Experimento</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Experimento</th>
                                <th>Análisis</th>
                                <th>P-Valor</th>
                                <th>Tamaño Efecto</th>
                                <th>Significancia</th>
                                <th>Potencia</th>
                                <th>Muestra</th>
                                <th>Significativo</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in df.iterrows():
            significance_class = "significant" if row['Significativo'] == 'Sí' else "not-significant"
            html += f"""
                            <tr class="{significance_class}">
                                <td>{row['Experimento']}</td>
                                <td>{row['Análisis']}</td>
                                <td>{row['P-Valor']:.4f}</td>
                                <td>{row['Tamaño_Efecto']:.3f}</td>
                                <td>{row['Significancia_Efecto']}</td>
                                <td>{row['Potencia']:.3f}</td>
                                <td>{row['Tamaño_Muestra']}</td>
                                <td>{row['Significativo']}</td>
                            </tr>
            """
        
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h2>📊 Análisis por Categoría</h2>
        """
        
        # Análisis por experimento
        for exp_name in ['BDI_Effectiveness', 'RAG_Precision', 'System_Performance', 'Integration_Effectiveness']:
            exp_data = df[df['Experimento'] == exp_name]
            if len(exp_data) > 0:
                significant_count = len(exp_data[exp_data['Significativo'] == 'Sí'])
                total_count = len(exp_data)
                mean_effect = exp_data['Tamaño_Efecto'].mean()
                
                html += f"""
                    <h3>{exp_name.replace('_', ' ')}</h3>
                    <p><strong>Análisis significativos:</strong> {significant_count}/{total_count} ({significant_count/total_count*100:.1f}%)</p>
                    <p><strong>Tamaño de efecto promedio:</strong> {mean_effect:.3f}</p>
                    <p><strong>Tiempo de ejecución:</strong> {self.execution_times.get(exp_name, 0):.2f} segundos</p>
                """
        
        html += """
                </div>
                
                <div class="recommendations">
                    <h3>🎯 Recomendaciones Principales</h3>
                    <ul>
                        <li><strong>Optimización BDI:</strong> Implementar estrategias de reconsideración de intentions basadas en los patrones identificados</li>
                        <li><strong>Mejora RAG:</strong> Optimizar sistemas RAG con menor precisión y implementar aprendizaje adaptativo</li>
                        <li><strong>Escalabilidad:</strong> Implementar optimizaciones para cargas extremas y balanceo de recursos</li>
                        <li><strong>Integración:</strong> Optimizar patrones de comunicación y persistencia de memoria</li>
                        <li><strong>Monitoreo:</strong> Implementar métricas continuas basadas en los hallazgos estadísticos</li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>📈 Métricas de Calidad</h2>
                    <p><strong>Potencia estadística promedio:</strong> {self.overall_stats['mean_power']:.3f} (objetivo: 0.8)</p>
                    <p><strong>Tamaño de efecto promedio:</strong> {self.overall_stats['mean_effect_size']:.3f}</p>
                    <p><strong>P-valor promedio:</strong> {self.overall_stats['mean_p_value']:.4f}</p>
                    <p><strong>Supuestos cumplidos:</strong> {len(df[df['Supuestos_Cumplidos'] == 'Sí'])}/{len(df)} ({len(df[df['Supuestos_Cumplidos'] == 'Sí'])/len(df)*100:.1f}%)</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_consolidated_visualizations(self, all_results: Dict[str, Any]):
        """Genera visualizaciones consolidadas de todos los experimentos."""
        print("\n📊 Generando visualizaciones consolidadas...")
        
        # Preparar datos para visualización
        viz_data = []
        
        for exp_name, exp_data in all_results.items():
            if exp_data['status'] == 'completed':
                for result in exp_data['results']:
                    viz_data.append({
                        'experiment': exp_name,
                        'analysis': result.experiment_name,
                        'p_value': result.p_value,
                        'effect_size': result.effect_size,
                        'power': result.power_achieved,
                        'sample_size': result.sample_size,
                        'significant': result.p_value < 0.05
                    })
        
        if not viz_data:
            print("⚠️ No hay datos para visualización")
            return
        
        df_viz = pd.DataFrame(viz_data)
        
        # Crear figura con múltiples subplots
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Análisis Consolidado de Experimentos Estadísticos', fontsize=16, fontweight='bold')
        
        # 1. Distribución de P-valores
        axes[0, 0].hist(df_viz['p_value'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        axes[0, 0].axvline(x=0.05, color='red', linestyle='--', label='α = 0.05')
        axes[0, 0].set_title('Distribución de P-valores')
        axes[0, 0].set_xlabel('P-valor')
        axes[0, 0].set_ylabel('Frecuencia')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Distribución de tamaños de efecto
        axes[0, 1].hist(df_viz['effect_size'], bins=15, alpha=0.7, color='lightgreen', edgecolor='black')
        axes[0, 1].set_title('Distribución de Tamaños de Efecto')
        axes[0, 1].set_xlabel('Tamaño de Efecto')
        axes[0, 1].set_ylabel('Frecuencia')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Potencia vs Tamaño de efecto
        scatter = axes[0, 2].scatter(df_viz['effect_size'], df_viz['power'], 
                                   c=df_viz['significant'], cmap='RdYlGn', alpha=0.7)
        axes[0, 2].set_title('Potencia vs Tamaño de Efecto')
        axes[0, 2].set_xlabel('Tamaño de Efecto')
        axes[0, 2].set_ylabel('Potencia')
        axes[0, 2].grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=axes[0, 2], label='Significativo')
        
        # 4. Análisis por experimento
        exp_counts = df_viz['experiment'].value_counts()
        axes[1, 0].bar(exp_counts.index, exp_counts.values, color='orange', alpha=0.7)
        axes[1, 0].set_title('Número de Análisis por Experimento')
        axes[1, 0].set_xlabel('Experimento')
        axes[1, 0].set_ylabel('Número de Análisis')
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].grid(True, alpha=0.3)
        
        # 5. Tasa de significancia por experimento
        significance_rates = df_viz.groupby('experiment')['significant'].mean()
        axes[1, 1].bar(significance_rates.index, significance_rates.values, color='purple', alpha=0.7)
        axes[1, 1].set_title('Tasa de Significancia por Experimento')
        axes[1, 1].set_xlabel('Experimento')
        axes[1, 1].set_ylabel('Proporción Significativa')
        axes[1, 1].tick_params(axis='x', rotation=45)
        axes[1, 1].grid(True, alpha=0.3)
        
        # 6. Tiempo de ejecución por experimento
        execution_times = list(self.execution_times.values())
        experiment_names = list(self.execution_times.keys())
        axes[1, 2].bar(experiment_names, execution_times, color='teal', alpha=0.7)
        axes[1, 2].set_title('Tiempo de Ejecución por Experimento')
        axes[1, 2].set_xlabel('Experimento')
        axes[1, 2].set_ylabel('Tiempo (segundos)')
        axes[1, 2].tick_params(axis='x', rotation=45)
        axes[1, 2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar visualización
        viz_file = os.path.join(self.output_dir, "visualizaciones_consolidadas.png")
        plt.savefig(viz_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Visualizaciones consolidadas guardadas en: {viz_file}")

def main():
    """Función principal para ejecutar la suite completa de experimentos."""
    print("🚀 Iniciando Suite Completa de Experimentos Estadísticos")
    print("="*80)
    
    # Crear ejecutor de experimentos
    runner = ExperimentRunner()
    
    # Ejecutar todos los experimentos
    results = runner.run_all_experiments()
    
    # Mostrar resumen final
    print("\n" + "="*80)
    print("🎯 RESUMEN FINAL DE LA SUITE DE EXPERIMENTOS")
    print("="*80)
    
    print("📊 Estadísticas Generales:")
    print(f"   - Experimentos completados: {runner.overall_stats['completed_experiments']}/{len(results)}")
    print(f"   - Análisis totales: {runner.overall_stats['total_analyses']}")
    
    if runner.overall_stats['total_analyses'] > 0:
        print(f"   - Análisis significativos: {runner.overall_stats['significant_analyses']} ({runner.overall_stats['significant_analyses']/runner.overall_stats['total_analyses']*100:.1f}%)")
        print(f"   - Potencia promedio: {runner.overall_stats.get('average_power', 0):.3f}")
        print(f"   - Tamaño de efecto promedio: {runner.overall_stats.get('average_effect_size', 0):.3f}")
    else:
        print("   - Análisis significativos: 0 (0.0%)")
        print("   - Potencia promedio: 0.000")
        print("   - Tamaño de efecto promedio: 0.000")
    
    print(f"   - Tiempo total: {runner.overall_stats.get('total_execution_time', 0):.2f} segundos")
    print(f"   - Resultados guardados en: {runner.output_dir}")
    
    print(f"\n📁 Archivos Generados:")
    print(f"   - Reporte HTML: {runner.output_dir}/reporte_final_experimentos.html")
    print(f"   - Datos CSV: {runner.output_dir}/resultados_detallados.csv")
    print(f"   - Análisis JSON: {runner.output_dir}/consolidated_analysis.json")
    print(f"   - Visualizaciones: {runner.output_dir}/visualizaciones_consolidadas.png")
    
    print(f"\n🎯 Principales Hallazgos:")
    
    # Identificar experimentos más significativos
    significant_experiments = []
    for exp_name, exp_data in results.items():
        if exp_data['status'] == 'completed':
            significant_count = sum(1 for r in exp_data['results'] if r.p_value < 0.05)
            if significant_count > 0:
                significant_experiments.append((exp_name, significant_count))
    
    significant_experiments.sort(key=lambda x: x[1], reverse=True)
    
    for exp_name, count in significant_experiments[:3]:
        print(f"   - {exp_name}: {count} análisis significativos")
    
    print(f"\n✅ Suite de experimentos completada exitosamente!")
    print("="*80)

if __name__ == "__main__":
    main() 