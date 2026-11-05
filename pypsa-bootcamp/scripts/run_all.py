"""Execute every bootcamp chapter end to end.

Converts each scripts/NN_*.py (jupytext percent format) to a notebook under
notebooks/ and runs it with nbconvert, so all outputs and figures are refreshed.

Usage (from the pypsa-bootcamp/ folder):
    python scripts/run_all.py            # run all chapters
    python scripts/run_all.py 05 07      # run only chapters 05 and 07
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
NOTEBOOKS = ROOT / "notebooks"
NOTEBOOKS.mkdir(exist_ok=True)


def chapters(selectors):
    for src in sorted(SCRIPTS.glob("[0-9][0-9]_*.py")):
        if selectors and not any(src.name.startswith(s) for s in selectors):
            continue
        yield src


def main():
    selectors = sys.argv[1:]
    for src in chapters(selectors):
        nb = NOTEBOOKS / (src.stem + ".ipynb")
        print(f"==> {src.name}")
        subprocess.run(["jupytext", "--to", "notebook", str(src), "-o", str(nb)],
                       check=True)
        subprocess.run(["jupyter", "nbconvert", "--to", "notebook", "--execute",
                        "--inplace", str(nb),
                        "--ExecutePreprocessor.timeout=600"], check=True)
    print("done.")


if __name__ == "__main__":
    main()
