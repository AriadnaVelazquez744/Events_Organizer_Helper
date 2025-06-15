import unittest
from datetime import datetime
from planner_rag import PlannerRAG, BudgetDistribution

class TestPlannerRAG(unittest.TestCase):
    def setUp(self):
        self.rag = PlannerRAG()

    def test_budget_distribution(self):
        """Prueba la distribución de presupuesto."""
        # Prueba distribución estándar
        distribution = self.rag.get_budget_distribution(100000)
        self.assertEqual(sum(distribution.values()), 100000)
        self.assertAlmostEqual(distribution["venue"], 40000)
        self.assertAlmostEqual(distribution["catering"], 30000)
        self.assertAlmostEqual(distribution["decor"], 15000)
        self.assertAlmostEqual(distribution["music"], 10000)
        self.assertAlmostEqual(distribution["other"], 5000)

        # Prueba distribución premium
        distribution = self.rag.get_budget_distribution(100000, "premium")
        self.assertEqual(sum(distribution.values()), 100000)
        self.assertAlmostEqual(distribution["venue"], 35000)
        self.assertAlmostEqual(distribution["catering"], 35000)
        self.assertAlmostEqual(distribution["decor"], 20000)
        self.assertAlmostEqual(distribution["music"], 5000)
        self.assertAlmostEqual(distribution["other"], 5000)

    def test_conflict_resolution(self):
        """Prueba la resolución de conflictos."""
        # Prueba conflicto de presupuesto
        strategies = self.rag.suggest_conflict_resolution(
            "budget_exceeded",
            {"current_budget": 100000, "required_budget": 120000}
        )
        self.assertTrue(len(strategies) > 0)
        self.assertTrue(any(s["strategy"] == "reduce_guest_count" for s in strategies))

        # Prueba conflicto de capacidad
        strategies = self.rag.suggest_conflict_resolution(
            "capacity_mismatch",
            {"venue_capacity": 100, "guest_count": 150}
        )
        self.assertTrue(len(strategies) > 0)
        self.assertTrue(any(s["strategy"] == "find_alternative_venue" for s in strategies))

    def test_timeline_recommendations(self):
        """Prueba las recomendaciones de timeline."""
        event_date = datetime(2024, 12, 15)
        recommendations = self.rag.get_timeline_recommendations(event_date)
        
        self.assertTrue("venue_booking" in recommendations)
        self.assertTrue("catering_booking" in recommendations)
        self.assertTrue("decor_planning" in recommendations)
        self.assertTrue("music_booking" in recommendations)

        # Verifica que las fechas son correctas
        self.assertEqual(recommendations["venue_booking"].month, 6)  # 6 meses antes
        self.assertEqual(recommendations["catering_booking"].month, 8)  # 4 meses antes
        self.assertEqual(recommendations["decor_planning"].month, 9)  # 3 meses antes
        self.assertEqual(recommendations["music_booking"].month, 10)  # 2 meses antes

    def test_success_patterns(self):
        """Prueba el sistema de patrones de éxito."""
        # Añade un patrón de éxito
        self.rag.update_success_pattern(
            "budget_management",
            {
                "total_budget": 100000,
                "distribution": {
                    "venue": 40000,
                    "catering": 30000,
                    "decor": 15000,
                    "music": 10000,
                    "other": 5000
                },
                "success_rate": 0.95
            }
        )

        # Busca casos similares
        similar_cases = self.rag.get_similar_cases(
            {
                "total_budget": 95000,
                "distribution": {
                    "venue": 38000,
                    "catering": 28500,
                    "decor": 14250,
                    "music": 9500,
                    "other": 4750
                }
            },
            "budget_management"
        )

        self.assertTrue(len(similar_cases) > 0)
        self.assertTrue(similar_cases[0]["similarity"] > 0.7)

    def test_similarity_calculation(self):
        """Prueba el cálculo de similitud."""
        case1 = {
            "budget": 100000,
            "guests": 100,
            "style": "modern",
            "preferences": ["vegetarian", "vegan"]
        }
        
        case2 = {
            "budget": 95000,
            "guests": 95,
            "style": "modern",
            "preferences": ["vegetarian", "gluten-free"]
        }

        similarity = self.rag._calculate_similarity(case1, case2)
        self.assertTrue(0 <= similarity <= 1)
        self.assertTrue(similarity > 0.5)  # Debería ser bastante similar

if __name__ == '__main__':
    unittest.main() 