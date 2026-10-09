# Power-to-X (PtX) | Model answers to Examination Subjects A, B and C

| File | Content |
|---|---|
| `PtX_Model_Answers.pdf` | Final PDF (compiled from LaTeX) |
| `word/PtX_Model_Answers.docx` | Word version; equations are native, editable Word equations |
| `latex/ptx_model_answers.tex` | LaTeX source (pdfLaTeX, works on Overleaf with the two logos and `flow_kasso.pdf`) |
| `latex/flow_kasso.tex` | Process-flow diagram of the Kassø plant (TikZ) |
| `tools/build_docx.py`, `tools/docx_filter.lua` | Rebuild the Word version from the LaTeX source |

Rebuild:

```
cd latex && pdflatex ptx_model_answers.tex && pdflatex ptx_model_answers.tex
cd .. && python3 tools/build_docx.py latex word/PtX_Model_Answers.docx
```
