# Mobile Computing – Assignment 5 (CO5)

This supplementary package supports the completed Assignment 5 documentation. It contains reproducible Python simulations for **Part B Tasks B1–B4**, generated CSV results, plots and editable diagram sources.

## Structure

```text
Mobile_Computing_Assignment_5_CO5_Supplementary/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   └── assignment5_simulation_suite.py
├── results/
│   ├── b1_background_decisions.csv
│   ├── b1_scheduler_summary.csv
│   ├── b2_workload_trace.csv
│   ├── b2_workload_summary.csv
│   ├── b3_small_instance_comparison.csv
│   ├── b3_scalability.csv
│   ├── b4_multimedia_decisions.csv
│   └── execution_summary.json
├── figures/
│   ├── a1–a5 architecture / flow diagrams
│   └── b1–b4 simulation charts
├── diagrams/
│   ├── graphviz_dot/   # editable Graphviz diagram sources
│   └── plantuml/       # editable PlantUML source equivalents
├── docs/
│   └── assumptions_and_output_map.md
├── tests/
│   ├── sample_inputs.json
│   └── verify_outputs.py
└── logs/
    └── simulation_run.log
```

## Requirements and execution

Python 3.10 or newer is recommended. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run the simulation suite from this directory:

```bash
python src/assignment5_simulation_suite.py
```

The script regenerates the CSV files in `results/` and the five computational charts in `figures/`. Five separate black-and-white architecture/flow diagrams are included as PNGs and as editable DOT / PlantUML source equivalents.

Verify the generated outputs:

```bash
python tests/verify_outputs.py
```

## Evidence policy

All Part B numerical outputs are **SIMULATED educational model outputs**. They are not Android device measurements, emulator logs, WorkManager timings, profiler captures, benchmark claims, or calibrated battery readings. Read `docs/assumptions_and_output_map.md` before interpreting them.

The completed assignment report is also included under `report/` for convenience and is supplied as separate DOCX and PDF deliverables.
