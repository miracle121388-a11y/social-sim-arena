# Complete manuscript

`main.pdf` is the compiled English paper. `paper_zh.md` explains the core argument in Chinese. The six sections are complete prose, with equations, Algorithm 1, three experimental questions, related work, limitations, and a complete 60-trial appendix.

## Build from the repository root

```powershell
.\.venv-research\Scripts\python.exe -I -B paper/generate_artifacts.py
.\.venv-research\Scripts\python.exe -I -B paper/build.py
.\.venv-research\Scripts\python.exe -I -B paper/validate_evidence.py
```

Requirements: the existing NumPy/Matplotlib research environment, pdfLaTeX and BibTeX on PATH, and the standard LaTeX packages named in `main.tex`. The build keeps TeX configuration, caches and temporary files in the research workspace. It does not run experiments or modify `method.py`.

For a standalone copy of the LaTeX project, run `pdflatex main.tex`, `bibtex main`, then `pdflatex main.tex` twice from its directory. All figures and tables needed for compilation are included. The Python regeneration scripts additionally require the repository's sealed result files and `workspace.py`.

## Evidence and interpretation

- `artifact_manifest.json`: exact canonical inputs and hashes; method hash checked before generation.
- `data_inventory.json`: inventory of every root `results/*.json`; historical and reproduction runs are not pooled as independent evidence.
- `numbers.json` and `tables/numbers.tex`: data-derived manuscript numbers.
- `figures/*.pdf`: vector plots; `tables/*.tex`: generated Booktabs and complete ledger tables.
- `qa/compilation.json`: actual compiler result and remaining diagnostics.
- `qa/evidence-validation.json`: rechecked Git/ledger records, frozen files, all 2,077 legacy hashes, and 38 recomputed activity/macro interval summaries.
- `qa/`: local PDF render and inspection records.

The paper reports synthetic evidence only. Official SocioVerse and SocialSim Arena remain NOT_EVALUATED. The original evaluation has calibration-confounded acquisition comparisons, so matched-prior controls are reported prominently. The selected mixture is nearly a point mass; a substantial acquisition or set-retention advantage is not claimed. Covariance scoring is an established variance-reduction identity, and general submodularity is explicitly disproved by a counterexample.

This is a neutral, anonymous conference-style manuscript, not an official NeurIPS/ICLR/KDD template or a claim of acceptance. Venue-specific length, style and author metadata should be set only once the intended venue is chosen. The previously open root `PAPER_TABLES.tex` is left unchanged.

`paper-source.zip` contains a portable TeX project, the compiled PDF, generated vector figures/tables, the Chinese explanation, and provenance summaries. Standard TeX compilation in the extracted directory does not require Python or the research repository. Python-based asset regeneration still uses the repository inputs listed above.

## Full Chinese translation

`main_zh.pdf` is the complete 15-page Chinese translation, including localized tables and figures. `paper_zh.md` remains the shorter core-logic companion. Run `python paper/generate_zh_assets.py` and `python paper/build_zh.py` from the research root to rebuild the Chinese version. The current XeLaTeX source uses font files from `C:/Windows/Fonts/` (SimSun, SimHei, FangSong, KaiTi); the PDF embeds fonts and can be read independently. `qa/zh/verification.json` records equality of displayed equations and table numbers with the English version. The previously distributed English source ZIP is unchanged.
