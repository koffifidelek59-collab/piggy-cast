"""Rebuild the datasets, then turn every case-study script into an executed notebook.

The scripts in scripts/csXX_*.py are the source (plain Python, "percent" format: easy to
read, diff and review). jupytext converts each one to notebooks/csXX_*.ipynb and nbconvert
executes it, so the notebooks always contain the outputs of the current code and data.

Run from the repository root:   python scripts/run_all.py
"""
import subprocess
import sys
import time
from pathlib import Path

import jupytext
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

only = sys.argv[1:]                      # optional: names of scripts to run, e.g. cs05 cs06
if not only:
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_datasets.py")], check=True)

for script in sorted((ROOT / "scripts").glob("cs*.py")):
    if only and not any(script.stem.startswith(o) for o in only):
        continue
    t0 = time.time()
    nb = jupytext.read(script)
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    ExecutePreprocessor(timeout=3600, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(NB)}})
    out = NB / (script.stem + ".ipynb")
    nbformat.write(nb, out)
    print(f"{out.name:45s} executed in {time.time() - t0:5.0f} s")
