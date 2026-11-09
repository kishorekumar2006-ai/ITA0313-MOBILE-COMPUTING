# Mobile Computing – Assignment 4 (CO4)

This repository contains the completed academic report and supporting materials for **Assignment 4A and Assignment 4B**.

- **Assignment 4A:** architectural analysis and design through structured reasoning.
- **Assignment 4B:** mobile systems engineering simulations covering operating-system behaviour, threading, runtime behaviour, security, power management and battery-aware tracking.

## Repository structure

```text
Mobile_Computing_Assignment_4_CO4_GitHub_Repository/
├── README.md
├── requirements.txt
├── .gitignore
├── reports/
│   ├── Assignment_4_CO4_Complete_Documentation.docx
│   └── Assignment_4_CO4_Complete_Documentation.pdf
├── src/
│   └── assignment4_simulation_suite.py
├── results/
│   └── 16 CSV simulation result files
├── figures/
│   └── 23 PNG figures and charts
├── diagrams/
│   ├── graphviz_dot/       # Editable Graphviz DOT source
│   └── plantuml/           # Editable PlantUML source equivalents
└── docs/
    ├── simulation_assumptions_and_output_map.md
    ├── GITHUB_UPLOAD_GUIDE.md
    └── SUBMISSION_CHECKLIST.md
```

## Requirements

- Python 3.10 or newer
- NumPy
- Matplotlib
- Git (only needed for command-line upload)

Install Python dependencies:

```bash
python -m pip install -r requirements.txt
```

## Re-run the Assignment 4B simulations

Run from the repository root:

```bash
python src/assignment4_simulation_suite.py
```

The script regenerates the CSV files in `results/` and simulation charts in `figures/`. The architecture diagrams are supplied separately as PNGs with editable DOT and PlantUML source files.

## Evidence and interpretation

**Assignment 4B results are simulated.** The Python models use deterministic educational assumptions. They are not physical-device measurements, Android/iOS emulator logs, ADB output, profiler captures, Perfetto traces, Battery Historian results or calibrated handset power measurements. See `docs/simulation_assumptions_and_output_map.md` for model assumptions, formulas, output mapping and limitations.

The report is provided in both DOCX and PDF formats under `reports/`. The supplementary files support the report; they do not replace it.

## GitHub upload

See [`docs/GITHUB_UPLOAD_GUIDE.md`](docs/GITHUB_UPLOAD_GUIDE.md) for the recommended upload steps and Git commands.
