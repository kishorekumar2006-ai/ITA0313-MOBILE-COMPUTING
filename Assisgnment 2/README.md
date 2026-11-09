# Mobile Computing Assignment 2 – CO2
## Python source code, figures and simulation results

This repository contains the reproducible Python source, figures and CSV data prepared for the Mobile Computing Assignment 2 (CO2), Questions 1–7.

### Repository contents
- `src/mobile_computing_co2_simulations.py` – complete Python source for the Q1–Q7 simulations and figure generation.
- `figures/` – seven output figures (Q1–Q7).
- `results/` – CSV data and simulation outputs for Q1–Q7.
- `docs/Assignment_2_CO2_Completed_Report.docx` and `.pdf` – completed assignment report copies.
- `docs/methodology_and_limitations.md` – model assumptions and academic limitations.
- `docs/group_submission_checklist.md` – checklist before submitting to faculty/GitHub.
- `requirements.txt` – Python package requirements.

### Setup
Use Python 3.9 or newer. From this folder, run:

```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the source:
```bash
python src/mobile_computing_co2_simulations.py
```

**Important:** the source script writes generated CSV and PNG files to `/mnt/data` as originally authored. For a local run, either change the `D` variable near the top of the script to the repository root, or copy the script to a suitable working directory and update `D`. The included `results/` and `figures/` folders already contain the generated outputs.

### GitHub upload
1. Extract the ZIP file.
2. Open the extracted folder in VS Code.
3. Review the files and run the script after installing requirements.
4. Create a GitHub repository, e.g. `mobile-computing-assignment-2-co2`.
5. Upload the **contents of this folder**, not just the ZIP file.

Optional Git commands:
```bash
git init
git add .
git commit -m "Add Mobile Computing CO2 Python simulations and results"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/mobile-computing-assignment-2-co2.git
git push -u origin main
```
Replace `YOUR-USERNAME` and the repository URL with the actual GitHub details.

### Academic integrity and interpretation
The included simulations use simplified teaching models and a fixed random seed (`20261104`). They are not field measurements or full standards-conformance simulations. Read the methodology and limitations file before interpreting the results. Both group members should understand the code, assumptions, tables and figures and should accurately record their contributions.
