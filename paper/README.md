# Learning from Earlier Actions: Layered Memory for ARC-AGI-3 Agents

Chongwei (Alan) Dai. Version of November 25, 2026.

The paper: [`Dai_Layered_Memory_for_ARC-AGI-3_Agents.pdf`](Dai_Layered_Memory_for_ARC-AGI-3_Agents.pdf)

## What is in this folder

| Files | What they are |
|---|---|
| `main.tex`, `metadata.tex`, `sections/`, `figures/`, `tables/`, `references.bib` | The paper's LaTeX source. Build it with `latexmk -pdf main.tex`. |
| `data/` | The records behind the paper's numbers: copies of result files from this repository's `reports/` folder, and the paper's own tables. |
| `verify_layered.py` | Recomputes the paper's scores, counts and comparisons from `data/` and checks them against the text. |
| `figures/make_result_figures.py` | Redraws the paper's four charts from `data/`. Needs Matplotlib. |
| `verify_continuation.py`, `verify_followup.py`, `analyze_results.py` | Checks for the historical appendices: the original 100-action baseline and the two-game Tycho follow-up. |
| `experiment_plan.yaml`, `schemas/` | The study record, and the reply schema that Appendix B refers to. |

## Checking the paper's numbers

```
cd paper
python3 verify_layered.py
```

The script needs only Python 3. It makes no model calls and uses no network. It prints one line for each group of
checks and stops with an error if any number in the paper does not follow from the data.

Two files say where the data comes from:

- `data/final_evidence_provenance.json` lists each source file in this repository with its hash at the commit the
  paper cites.
- `data/figure_sources.json` says where each figure's images and quoted text come from.

## What the checks do not do

They do not run the model again. The run logs, with every request and reply, are not in this repository; the
paper says which statements rest on them.

## Which commit the paper cites

The paper cites this repository at commit `17d00cf`, which holds the code and the evidence. This folder was added
after that commit, so the paper's links do not include it.
