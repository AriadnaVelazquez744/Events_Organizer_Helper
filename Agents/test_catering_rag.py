import unittest
from datetime import datetime
from catering_rag import CateringRAG, MenuPattern, DietaryRestriction

class TestCateringRAG(unittest.TestCase):
    def setUp(self):
        self.rag = CateringRAG("test_catering_knowledge.json")

    def test_menu_recommendation(self):
        """Prueba la recomendación de menús."""
        # Prueba menú estándar
        recommendation = self.rag.get_menu_recommendation(
            budget=10000,
            guest_count=100,
            dietary_requirements=['regular', 'vegetariano'],
            style='standard'
        )
        
        self.assertEqual(recommendation['style'], 'standard')
        self.assertTrue(len(recommendation['courses']) > 0)
        self.assertTrue('vegetariano' in recommendation['dietary_options'])
        self.assertTrue(recommendation['estimated_cost'] > 0)
        
        # Prueba menú premium
        recommendation = self.rag.get_menu_recommendation(
            budget=20000,
            guest_count=80,
            dietary_requirements=['regular', 'vegetariano', 'vegano'],
            style='premium'
        )
        
        self.assertEqual(recommendation['style'], 'premium')
        self.assertTrue('vegano' in recommendation['dietary_options'])
        self.assertTrue(len(recommendation['courses']) > 3)  # Premium tiene más cursos

    def test_dietary_restrictions(self):
        """Prueba el manejo de restricciones dietéticas."""
        # Prueba alternativas para restricciones
        alternatives = self.rag.suggest_dietary_alternatives(['vegetariano', 'sin_gluten'])
        
        self.assertTrue('vegetariano' in alternatives)
        self.assertTrue('sin_gluten' in alternatives)
        self.assertTrue(len(alternatives['vegetariano']['alternatives']) > 0)
        self.assertTrue(alternatives['vegetariano']['cost_impact'] > 1.0)

    def test_pattern_updates(self):
        """Prueba la actualización de patrones."""
        # Crea un nuevo patrón
        menu_data = {
            'style': 'test_style',
            'courses': ['entrada', 'principal'],
            'dietary_options': ['regular'],
            'estimated_cost': 5000,
            'guest_count': 50
        }
        
        # Actualiza con éxito
        self.rag.update_success_pattern(menu_data, True)
        
        # Verifica que se creó el patrón
        recommendation = self.rag.get_menu_recommendation(
            budget=5000,
            guest_count=50,
            dietary_requirements=['regular'],
            style='test_style'
        )
        
        self.assertEqual(recommendation['style'], 'test_style')
        self.assertEqual(len(recommendation['courses']), 2)

    def test_similar_cases(self):
        """Prueba la búsqueda de casos similares."""
        menu_data = {
            'style': 'standard',
            'courses': ['entrada', 'plato_principal', 'postre'],
            'dietary_options': ['regular', 'vegetariano']
        }
        
        similar_cases = self.rag.get_similar_cases(menu_data)
        
        self.assertTrue(len(similar_cases) > 0)
        self.assertTrue(all(isinstance(case[0], MenuPattern) for case in similar_cases))
        self.assertTrue(all(0 <= case[1] <= 1 for case in similar_cases))

    def test_cost_calculation(self):
        """Prueba el cálculo de costos."""
        pattern = MenuPattern(
            style='test',
            courses=['entrada', 'principal'],
            dietary_options=['regular', 'vegetariano'],
            price_range=(50.0, 100.0),
            guest_count_range=(50, 100),
            success_rate=0.8,
            last_used=datetime.now().isoformat(),
            usage_count=0
        )
        
        cost = self.rag._calculate_menu_cost(pattern, 5000, 50)
        
        self.assertTrue(cost > 0)
        self.assertTrue(cost <= 5000 * 1.1)  # Considerando el factor dietético

    def test_custom_menu_generation(self):
        """Prueba la generación de menús personalizados."""
        # Prueba con parámetros fuera de los rangos estándar
        menu = self.rag._generate_custom_menu(
            budget=5000,
            guest_count=20,  # Menos invitados que el mínimo
            dietary_requirements=['vegano', 'sin_gluten'],
            style='custom'
        )
        
        self.assertEqual(menu['style'], 'custom')
        self.assertTrue('vegano' in menu['dietary_options'])
        self.assertTrue('sin_gluten' in menu['dietary_options'])
        self.assertEqual(menu['estimated_cost'], 5000)

if __name__ == '__main__':
    unittest.main() 