import unittest
from agents.decor.decor_rag import DecorRAG, MenuPattern
from datetime import datetime

class TestDecorRAG(unittest.TestCase):
    def setUp(self):
        self.rag = DecorRAG("test_decor_knowledge.json")
        self.rag.menu_patterns = []  # Limpiar patrones para tests

    def test_cost_calculation(self):
        """Test que verifica el cálculo de costos."""
        # Test con presupuesto bajo
        recommendation = self.rag.get_decor_recommendation(
            budget=1000,
            guest_count=50,
            style="classic"
        )
        self.assertIsNotNone(recommendation)
        self.assertLessEqual(recommendation["estimated_cost"], 1000)

        # Test con presupuesto alto
        recommendation = self.rag.get_decor_recommendation(
            budget=5000,
            guest_count=100,
            style="premium"
        )
        self.assertIsNotNone(recommendation)
        self.assertLessEqual(recommendation["estimated_cost"], 5000)

    def test_decor_recommendation(self):
        """Test que verifica las recomendaciones de decoración."""
        # Test estilo clásico
        recommendation = self.rag.get_decor_recommendation(
            budget=2000,
            guest_count=75,
            style="classic"
        )
        self.assertIsNotNone(recommendation)
        self.assertGreaterEqual(len(recommendation["decorations"]), 3)
        self.assertGreaterEqual(len(recommendation["paper_goods"]), 2)
        self.assertGreaterEqual(len(recommendation["rentals"]), 3)

        # Test estilo premium
        recommendation = self.rag.get_decor_recommendation(
            budget=4000,
            guest_count=75,
            style="premium"
        )
        self.assertIsNotNone(recommendation)
        self.assertGreaterEqual(len(recommendation["decorations"]), 5)
        self.assertGreaterEqual(len(recommendation["paper_goods"]), 3)
        self.assertGreaterEqual(len(recommendation["rentals"]), 4)

    def test_similar_cases(self):
        """Test que verifica la búsqueda de casos similares."""
        # Crear algunos patrones de prueba
        pattern1 = MenuPattern(
            style="classic",
            courses=["entrada", "plato_principal", "postre"],
            dietary_options=["regular", "vegetariano"],
            price_range=(50.0, 100.0),
            guest_count_range=(50, 200),
            success_rate=0.8,
            last_used=datetime.now().isoformat(),
            usage_count=5
        )
        pattern2 = MenuPattern(
            style="premium",
            courses=["entrada", "sopa", "plato_principal", "ensalada", "postre"],
            dietary_options=["regular", "vegetariano", "vegano"],
            price_range=(100.0, 200.0),
            guest_count_range=(30, 150),
            success_rate=0.9,
            last_used=datetime.now().isoformat(),
            usage_count=3
        )
        self.rag.menu_patterns = [pattern1, pattern2]

        # Test búsqueda de casos similares
        similar = self.rag.find_similar_cases(
            style="classic",
            guest_count=100,
            budget=75.0
        )
        self.assertIsNotNone(similar)
        self.assertGreater(len(similar), 0)
        self.assertLessEqual(similar[0]["similarity"], 1.0)
        self.assertGreaterEqual(similar[0]["similarity"], 0.0)

    def test_update_success_pattern(self):
        """Test que verifica la actualización de patrones de éxito."""
        # Crear un patrón inicial
        initial_pattern = MenuPattern(
            style="classic",
            courses=["entrada", "plato_principal", "postre"],
            dietary_options=["regular", "vegetariano"],
            price_range=(50.0, 100.0),
            guest_count_range=(50, 200),
            success_rate=0.8,
            last_used=datetime.now().isoformat(),
            usage_count=1
        )
        self.rag.menu_patterns = [initial_pattern]

        # Actualizar el patrón
        self.rag.update_success_pattern(
            {
                "style": "classic",
                "decorations": ["flores", "velas", "centros"],
                "paper_goods": ["invitaciones", "menús"],
                "rentals": ["mesas", "sillas", "manteles"],
                "estimated_cost": 75.0,
                "guest_count": 100
            },
            True
        )

        # Verificar que el patrón se actualizó correctamente
        updated_pattern = self.rag.menu_patterns[0]
        self.assertEqual(updated_pattern.usage_count, 2)
        self.assertGreater(updated_pattern.success_rate, 0.8)

if __name__ == '__main__':
    unittest.main() 