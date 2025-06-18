# Experiments Folder Organization

## Overview

This folder contains all experiment-related files for the Events Organizer Helper project. The experiments are organized to maintain clear separation between framework code, individual experiments, and their results.

## Folder Structure

```
experiments/
├── framework/
│   ├── __init__.py
│   └── experimental_framework.py          # Core experiment framework
├── experiments/
│   ├── __init__.py
│   ├── experiment_2_bdi_effectiveness.py  # BDI system effectiveness analysis
│   ├── experiment_3_rag_precision.py      # RAG system precision analysis
│   ├── experiment_5_system_performance.py # System performance analysis
│   └── experiment_6_integration_effectiveness.py # Integration effectiveness analysis
├── results/
│   ├── bdi_effectiveness/                 # BDI experiment results
│   ├── rag_precision/                     # RAG experiment results
│   ├── system_performance/                # Performance experiment results
│   ├── integration_effectiveness/         # Integration experiment results
│   ├── consolidated_analysis.json         # Consolidated analysis results
│   ├── resultados_detallados.csv          # Detailed results in CSV format
│   ├── reporte_final_experimentos.html    # Final HTML report
│   └── visualizaciones_consolidadas.png   # Consolidated visualizations
├── run_all_experiments.py                 # Main script to run all experiments
├── __init__.py
└── README_EXPERIMENTS.md                  # This file
```

## Key Features

### 1. Framework (`framework/`)

- **experimental_framework.py**: Contains the core experiment infrastructure.
  - `BaseExperiment`: Base class for all experiments.
  - `ExperimentConfig`: Configuration dataclass.
  - `ExperimentResult`: Result dataclass.
  - `StatisticalValidator`: Statistical validation utilities.
  - `EffectSizeCalculator`: Effect size calculation utilities.
  - `PowerAnalyzer`: Statistical power analysis.
  - `DataCollector`: Data collection utilities.
  - `ExperimentReporter`: Report generation utilities.

### 2. Individual Experiments (`experiments/`)

Each experiment file contains:

- A specific experiment class inheriting from `BaseExperiment`.
- Synthetic data generation methods.
- Statistical analysis methods.
- A main function to run the experiment.

**Available Experiments:**

- **BDI Effectiveness**: Analyzes the effectiveness of the Belief-Desire-Intention cycle.
- **RAG Precision**: Analyzes the precision of Retrieval-Augmented Generation systems.
- **System Performance**: Analyzes system scalability and performance metrics.
- **Integration Effectiveness**: Analyzes the effectiveness of system integration components.

### 3. Results (`results/`)

Each experiment type has its own subfolder containing:

- JSON data files with experiment results.
- HTML reports with detailed analysis.
- PNG visualization files.
- CSV files with processed data.

## Usage

### Running Individual Experiments

```python
# Example: Running BDI effectiveness experiment
from experiments.experiments.experiment_2_bdi_effectiveness import run_bdi_experiments

# Create mock system components
system_components = {
    'planner': None,
    'memory': None,
    'bus': None
}

# Run the experiment
results = run_bdi_experiments(system_components)
```

### Running All Experiments

```python
# From the experiments directory
from run_all_experiments import ExperimentRunner

# Create runner with custom output directory
runner = ExperimentRunner(output_dir="results")

# Run all experiments
all_results = runner.run_all_experiments()
```

### Command Line Usage

```bash
# Run all experiments
cd experiments
python run_all_experiments.py

# Run individual experiment
python -m experiments.experiment_2_bdi_effectiveness
```

## Output Organization

### File Naming Convention

- **Data files**: `{experiment_name}_{timestamp}_data.json`
- **Reports**: `{experiment_name}_{timestamp}_report.html`
- **Visualizations**: `{experiment_name}_{timestamp}_plots.png`

### Result Structure

Each experiment generates:

1. **Raw data**: JSON files with all collected metrics.
2. **Statistical analysis**: P-values, effect sizes, confidence intervals.
3. **Visualizations**: Plots showing distributions, correlations, and trends.
4. **Reports**: HTML reports with detailed analysis and recommendations.

## Configuration

### Experiment Configuration

Each experiment uses `ExperimentConfig` with parameters:

- `name`: Experiment identifier.
- `description`: Human-readable description.
- `alpha`: Significance level (default: 0.05).
- `power`: Desired statistical power (default: 0.8).
- `effect_size`: Expected effect size (default: 0.5).
- `min_sample_size`: Minimum sample size (default: 30).
- `max_sample_size`: Maximum sample size (default: 1000).
- `random_seed`: Random seed for reproducibility (default: 42).

### Output Directory Configuration

- Each experiment automatically creates its output directory.
- Results are organized by experiment type.
- Consolidated results are stored in the main results directory.

## Dependencies

### Required Python Packages

- `numpy`: Numerical computations.
- `pandas`: Data manipulation.
- `matplotlib`: Plotting.
- `seaborn`: Statistical visualizations.
- `scipy`: Statistical tests.
- `scikit-learn`: Machine learning utilities.
- `statsmodels`: Statistical modeling.
- `networkx`: Network analysis (for integration experiments).

### Installation

```bash
uv add -r requirements_experiments.txt 
```

## Best Practices

### 1. Adding New Experiments

1. Create a new file in `experiments/` following the naming convention.
2. Inherit from `BaseExperiment`.
3. Implement required methods (`run()`, data generation, analysis).
4. Add a main function following the pattern of existing experiments.
5. Update `run_all_experiments.py` to include the new experiment.

### 2. Result Management

- Always use the `output_dir` parameter when creating experiments.
- Use descriptive file names with timestamps.
- Include comprehensive metadata in result files.
- Generate both raw data and processed results.

### 3. Statistical Rigor

- Always validate statistical assumptions.
- Report effect sizes and confidence intervals.
- Include power analysis results.
- Provide clear conclusions and recommendations.

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure all dependencies are installed.
2. **Path issues**: Make sure you're running from the correct directory.
3. **Memory issues**: Large experiments may require more memory.
4. **Statistical warnings**: Check data quality and sample sizes.

### Debugging

- Enable debug logging in experiment classes.
- Check intermediate results in data files.
- Verify statistical assumptions are met.
- Review generated reports for insights.

## Contributing

When adding new experiments:

1. Follow the existing code structure.
2. Include comprehensive documentation.
3. Add appropriate error handling.
4. Ensure reproducible results.
5. Update this README with new information.

## License

This experiments framework is part of the Events Organizer Helper project and follows the same licensing terms.
