from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import time
from Crawler.quality_validator import DataQualityValidator

class DataQualityMonitor:
    def __init__(self, quality_validator: DataQualityValidator):
        self.quality_validator = quality_validator
        self.alert_thresholds = {
            "low_quality_threshold": 0.5,  # Alertar si score < 0.5
            "enrichment_failure_threshold": 0.3,  # Alertar si enriquecimiento no mejora
            "stale_data_threshold": 60,  # Alertar si datos > 60 días
            "missing_critical_fields_threshold": 3  # Alertar si faltan > 3 campos críticos
        }
        
        self.alerts = []
        self.quality_history = []
        self.enrichment_history = []

    def monitor_data_quality(self, data: Dict[str, Any], data_type: str, source_url: str = None) -> Dict[str, Any]:
        """Monitorea la calidad de los datos y genera alertas si es necesario."""
        monitoring_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": data_type,
            "source_url": source_url,
            "quality_score": 0.0,
            "alerts_generated": [],
            "recommendations": []
        }
        
        # Validar calidad
        quality_result = self.quality_validator.validate_data_quality(data, data_type)
        monitoring_result["quality_score"] = quality_result["overall_score"]
        
        # Generar alertas
        alerts = self._generate_alerts(quality_result, data, data_type, source_url)
        monitoring_result["alerts_generated"] = alerts
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(quality_result, data, data_type)
        monitoring_result["recommendations"] = recommendations
        
        # Registrar en historial
        self.quality_history.append(monitoring_result)
        
        # Mantener solo los últimos 1000 registros
        if len(self.quality_history) > 1000:
            self.quality_history = self.quality_history[-1000:]
        
        return monitoring_result

    def monitor_enrichment_process(self, original_data: Dict[str, Any], enriched_data: Dict[str, Any], 
                                 data_type: str, enrichment_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Monitorea el proceso de enriquecimiento."""
        enrichment_monitoring = {
            "timestamp": datetime.utcnow().isoformat(),
            "data_type": data_type,
            "original_score": enrichment_stats.get("original_score", 0.0),
            "enriched_score": enrichment_stats.get("enriched_score", 0.0),
            "improvement": enrichment_stats.get("improvement", 0.0),
            "fields_added": enrichment_stats.get("fields_added", 0),
            "enrichment_success": False,
            "alerts": []
        }
        
        # Verificar si el enriquecimiento fue exitoso
        if enrichment_stats.get("improvement", 0.0) > 0.1:  # Mejora significativa
            enrichment_monitoring["enrichment_success"] = True
        else:
            # Generar alerta de enriquecimiento fallido
            alert = {
                "type": "enrichment_failure",
                "severity": "warning",
                "message": f"Enriquecimiento no mejoró significativamente la calidad de datos",
                "details": {
                    "original_score": enrichment_stats.get("original_score", 0.0),
                    "enriched_score": enrichment_stats.get("enriched_score", 0.0),
                    "improvement": enrichment_stats.get("improvement", 0.0)
                }
            }
            enrichment_monitoring["alerts"].append(alert)
        
        # Registrar en historial
        self.enrichment_history.append(enrichment_monitoring)
        
        # Mantener solo los últimos 500 registros
        if len(self.enrichment_history) > 500:
            self.enrichment_history = self.enrichment_history[-500:]
        
        return enrichment_monitoring

    def _generate_alerts(self, quality_result: Dict[str, Any], data: Dict[str, Any], 
                        data_type: str, source_url: str = None) -> List[Dict[str, Any]]:
        """Genera alertas basadas en los resultados de calidad."""
        alerts = []
        
        # Alerta por baja calidad general
        if quality_result["overall_score"] < self.alert_thresholds["low_quality_threshold"]:
            alert = {
                "type": "low_quality",
                "severity": "high",
                "message": f"Datos de {data_type} con calidad muy baja (score: {quality_result['overall_score']:.2f})",
                "details": {
                    "score": quality_result["overall_score"],
                    "missing_fields": quality_result["missing_fields"],
                    "invalid_fields": quality_result["invalid_fields"],
                    "source_url": source_url
                }
            }
            alerts.append(alert)
        
        # Alerta por campos críticos faltantes
        critical_missing = len([f for f in quality_result["missing_fields"] 
                              if f in self.quality_validator.critical_fields.get(data_type, [])])
        if critical_missing >= self.alert_thresholds["missing_critical_fields_threshold"]:
            alert = {
                "type": "missing_critical_fields",
                "severity": "high",
                "message": f"Faltan {critical_missing} campos críticos en datos de {data_type}",
                "details": {
                    "missing_critical_fields": critical_missing,
                    "missing_fields": quality_result["missing_fields"],
                    "source_url": source_url
                }
            }
            alerts.append(alert)
        
        # Alerta por datos desactualizados
        if not quality_result["is_fresh"]:
            alert = {
                "type": "stale_data",
                "severity": "medium",
                "message": f"Datos de {data_type} desactualizados ({quality_result.get('age_days', 0)} días)",
                "details": {
                    "age_days": quality_result.get("age_days", 0),
                    "freshness_threshold": self.alert_thresholds["stale_data_threshold"],
                    "source_url": source_url
                }
            }
            alerts.append(alert)
        
        # Alerta por datos incompletos
        if quality_result["completeness_score"] < 0.5:
            alert = {
                "type": "incomplete_data",
                "severity": "medium",
                "message": f"Datos de {data_type} muy incompletos (completitud: {quality_result['completeness_score']:.2f})",
                "details": {
                    "completeness_score": quality_result["completeness_score"],
                    "missing_fields": quality_result["missing_fields"],
                    "source_url": source_url
                }
            }
            alerts.append(alert)
        
        # Registrar alertas globalmente
        for alert in alerts:
            alert["timestamp"] = datetime.utcnow().isoformat()
            alert["data_type"] = data_type
            self.alerts.append(alert)
        
        return alerts

    def _generate_recommendations(self, quality_result: Dict[str, Any], data: Dict[str, Any], 
                                data_type: str) -> List[str]:
        """Genera recomendaciones para mejorar la calidad de los datos."""
        recommendations = []
        
        # Recomendaciones basadas en campos faltantes
        missing_fields = quality_result["missing_fields"]
        if "price" in missing_fields:
            recommendations.append("Buscar información de precios en sitios web oficiales o directorios")
        if "capacity" in missing_fields:
            recommendations.append("Verificar capacidad en sitios de reservas o contactar directamente")
        if "location" in missing_fields:
            recommendations.append("Buscar dirección en Google Maps o directorios locales")
        
        # Recomendaciones basadas en frescura
        if not quality_result["is_fresh"]:
            recommendations.append("Actualizar datos desde la fuente original")
        
        # Recomendaciones basadas en precisión
        if quality_result["accuracy_score"] < 0.8:
            recommendations.append("Verificar y corregir datos inconsistentes")
        
        # Recomendaciones generales
        if quality_result["overall_score"] < 0.6:
            recommendations.append("Considerar enriquecimiento automático con fuentes externas")
        
        return recommendations

    def get_quality_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Analiza tendencias de calidad en las últimas horas."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_data = [
            record for record in self.quality_history
            if datetime.fromisoformat(record["timestamp"]) > cutoff_time
        ]
        
        if not recent_data:
            return {"message": "No hay datos recientes para análisis"}
        
        # Calcular estadísticas
        scores = [record["quality_score"] for record in recent_data]
        avg_score = sum(scores) / len(scores)
        
        # Análisis por tipo de dato
        by_type = {}
        for record in recent_data:
            data_type = record["data_type"]
            if data_type not in by_type:
                by_type[data_type] = {"count": 0, "scores": []}
            by_type[data_type]["count"] += 1
            by_type[data_type]["scores"].append(record["quality_score"])
        
        # Calcular promedios por tipo
        for data_type in by_type:
            by_type[data_type]["avg_score"] = sum(by_type[data_type]["scores"]) / len(by_type[data_type]["scores"])
        
        # Análisis de alertas
        recent_alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]
        
        alert_summary = {}
        for alert in recent_alerts:
            alert_type = alert["type"]
            if alert_type not in alert_summary:
                alert_summary[alert_type] = {"count": 0, "severity_counts": {}}
            alert_summary[alert_type]["count"] += 1
            
            severity = alert["severity"]
            if severity not in alert_summary[alert_type]["severity_counts"]:
                alert_summary[alert_type]["severity_counts"][severity] = 0
            alert_summary[alert_type]["severity_counts"][severity] += 1
        
        return {
            "time_period_hours": hours,
            "total_records": len(recent_data),
            "overall_avg_score": avg_score,
            "by_data_type": by_type,
            "alert_summary": alert_summary,
            "trend_analysis": self._analyze_trends(recent_data)
        }

    def _analyze_trends(self, recent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analiza tendencias en los datos recientes."""
        if len(recent_data) < 2:
            return {"message": "Insuficientes datos para análisis de tendencias"}
        
        # Ordenar por timestamp
        sorted_data = sorted(recent_data, key=lambda x: x["timestamp"])
        
        # Calcular tendencia de scores
        scores = [record["quality_score"] for record in sorted_data]
        
        # Tendencia simple (último vs primero)
        if len(scores) >= 2:
            trend_direction = "improving" if scores[-1] > scores[0] else "declining"
            trend_magnitude = abs(scores[-1] - scores[0])
        else:
            trend_direction = "stable"
            trend_magnitude = 0.0
        
        # Detectar patrones
        patterns = []
        if len(scores) >= 5:
            # Detectar si hay una tendencia consistente
            recent_avg = sum(scores[-5:]) / 5
            earlier_avg = sum(scores[:5]) / 5
            if recent_avg > earlier_avg + 0.1:
                patterns.append("Mejora consistente en calidad")
            elif recent_avg < earlier_avg - 0.1:
                patterns.append("Deterioro consistente en calidad")
        
        return {
            "trend_direction": trend_direction,
            "trend_magnitude": trend_magnitude,
            "patterns_detected": patterns,
            "score_range": {"min": min(scores), "max": max(scores)}
        }

    def get_active_alerts(self, severity_filter: str = None) -> List[Dict[str, Any]]:
        """Obtiene alertas activas, opcionalmente filtradas por severidad."""
        if severity_filter:
            return [alert for alert in self.alerts if alert["severity"] == severity_filter]
        return self.alerts

    def clear_old_alerts(self, days: int = 7):
        """Limpia alertas antiguas."""
        cutoff_time = datetime.utcnow() - timedelta(days=days)
        self.alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) > cutoff_time
        ]

    def export_monitoring_report(self, hours: int = 24) -> Dict[str, Any]:
        """Exporta un reporte completo de monitoreo."""
        trends = self.get_quality_trends(hours)
        active_alerts = self.get_active_alerts()
        
        report = {
            "report_timestamp": datetime.utcnow().isoformat(),
            "time_period_hours": hours,
            "summary": {
                "total_alerts": len(active_alerts),
                "high_severity_alerts": len([a for a in active_alerts if a["severity"] == "high"]),
                "overall_quality_score": trends.get("overall_avg_score", 0.0)
            },
            "trends": trends,
            "active_alerts": active_alerts,
            "recommendations": self._generate_system_recommendations(trends, active_alerts)
        }
        
        return report

    def _generate_system_recommendations(self, trends: Dict[str, Any], alerts: List[Dict[str, Any]]) -> List[str]:
        """Genera recomendaciones a nivel de sistema."""
        recommendations = []
        
        # Basadas en tendencias
        if trends.get("trend_analysis", {}).get("trend_direction") == "declining":
            recommendations.append("La calidad de datos está disminuyendo. Revisar fuentes y procesos de extracción")
        
        # Basadas en alertas
        high_severity_count = len([a for a in alerts if a["severity"] == "high"])
        if high_severity_count > 10:
            recommendations.append("Muchas alertas de alta severidad. Revisar configuración de validación")
        
        # Basadas en distribución de calidad
        overall_score = trends.get("overall_avg_score", 0.0)
        if overall_score < 0.6:
            recommendations.append("Calidad general baja. Considerar mejorar fuentes de datos o enriquecimiento")
        
        return recommendations 