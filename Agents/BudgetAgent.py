
class BudgetOptimizerAgent:
    def __init__(self, total_budget, preferences):
        self.total_budget = total_budget
        self.preferences = preferences
        self.domains = {
            k: (v['min'], v['max']) for k, v in preferences.items()
        }
        self.weights = {
            k: v['importancia'] for k, v in preferences.items()
        }

    def fitness(self, allocation):
        penalty = 0
        total = sum(allocation.values())

        if total > self.total_budget:
            penalty += (total - self.total_budget) * 10  # castigo fuerte

        score = 0
        for k in allocation:
            ideal = self.weights[k] * self.total_budget
            diff = abs(ideal - allocation[k])
            score -= diff  # queremos acercarnos al ideal

        return -penalty + score

    def solve_with_genetic_algorithm(self, generations=100, population_size=30):
        # Cada individuo es un dict de asignaciones
        import random

        def create_individual():
            return {
                k: random.uniform(*self.domains[k]) for k in self.domains
            }

        def mutate(individual, rate=0.1):
            for k in individual:
                if random.random() < rate:
                    delta = random.uniform(-0.1, 0.1) * (self.domains[k][1] - self.domains[k][0])
                    individual[k] = min(max(individual[k] + delta, self.domains[k][0]), self.domains[k][1])

        population = [create_individual() for _ in range(population_size)]

        for _ in range(generations):
            population.sort(key=self.fitness, reverse=True)
            next_gen = population[:10]  # elitismo

            while len(next_gen) < population_size:
                p1, p2 = random.sample(population[:15], 2)
                child = {
                    k: (p1[k] + p2[k]) / 2 for k in p1
                }
                mutate(child)
                next_gen.append(child)

            population = next_gen

        best = max(population, key=self.fitness)
        return best
