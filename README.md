# Replication materials

### Diffusion Before Adoption: A Model of Compositional Latent Diffusion

Model engine, experiment scripts, analysis and figure code, per-replication output for every reported cell, and an environment specification.

**Author and citation details are withheld while the article is under blind review.**

---

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # or requirements-lock.txt for exact versions
python verify_reported_values.py         # recomputes every reported value from stored output
```

`verify_reported_values.py` is the script the article refers to. It reads only the CSVs under `results/`, recomputes each reported quantity (deriving contrasts and standard errors from per-replication data rather than from summaries), compares against the value printed in the article, and exits nonzero on any mismatch. It checks **97 values** and takes a few seconds. It does not re-run the simulation.

To re-run the model instead, see "Reproducing a result from scratch" below.

---

## What is here

| Path | Contents |
|---|---|
| `abm/` | The model engine. `model.py` is the whole simulation; there is no second implementation. |
| `token_model.py` | Self-contained token-memory model for the three-readiness-rule experiment. |
| `explore_*.py` | One script per reported experiment. Each writes to a timestamped directory under `results/`. |
| `verify_*.py` | Verification. See below. |
| `make_manuscript_figures.py` | Regenerates every figure in the article and its data audit. |
| `results/` | Per-replication output for every reported cell. See `results/README.md` for which sweeps are canonical. |
| `tests/` | 25 structural tests. |
| `viewer/`, `abm/server.py` | Optional live viewer. Not needed for replication. |
| `docx_tooling/` | Scripts that folded results into the authors' private working document. Included for transparency about how numbers reached the write-up. They operate on a document not distributed here and will not run. |
| `exploratory/` | Superseded exploratory scripts from the build phase. Retained so the record is complete; none produces a reported result. |

---

## Verification

Five independent checks. All should pass on a clean checkout.

| Command | What it establishes |
|---|---|
| `python verify_reported_values.py` | Every value in the article matches stored output. 97 checks. |
| `python -m pytest -q` | Structural correctness of network construction, requirement sets, capacity accounting, metrics. 25 tests. |
| `python verify_mechanisms.py` | Each optional mechanism does what it is documented to do, and nothing when off. 39 assertions. |
| `python verify_noop.py` | Every additive engine change is byte-identical to the prior model when disabled. 18 paths. |
| `python verify_token_arms.py` | The three readiness arms share one token history at every tick, including component and sender labels. 9,030 checks. |

The last is the load-bearing one for the article's identification claim: if the arms ever diverge in what they hold, the comparison is between different worlds.

---

## Where each result comes from

Main-text figures and the code and data behind them.

| Article element | Produced by | Data |
|---|---|---|
| Figure 1, conceptual architecture | `make_manuscript_figures.py::figure1` | none, schematic |
| Figure 2, propagation before manifestation | `make_manuscript_figures.py::figure2` | `results/20260731-endogenous/`, `results/20260816-carrier-diagnostics-endo/` |
| Figure 3, retention governs conversion | `make_manuscript_figures.py::figure3` | `results/20260730-102229-comments/` |
| Figure 4, content identity vs source diversity | `make_manuscript_figures.py::figure4` | `results/20260816-sourcenonredundant/` |
| Figure 5, retention and the return to transmission | `make_manuscript_figures.py::figure5` | `results/20260730-102229-comments/`, `results/20260730-093338-full/` |
| Figure S1, carrier threshold sensitivity | `make_manuscript_figures.py::figureS_carriers` | both `carrier-diagnostics` directories |
| Figure S2, manifest advocates | `make_manuscript_figures.py::figureS_advocates` | `results/20260814-changeagent/` |
| Table 1 | conceptual, no data | none |

Main-text results and the experiment that produced them.

| Result | Script | Output directory |
|---|---|---|
| Carrier trajectory, threshold sensitivity, sender-state instrumentation | `explore_carrier_diagnostics.py` | `20260816-carrier-diagnostics{,-endo}` |
| Three readiness rules over one token history | `explore_sourcenonredundant.py` | `20260816-sourcenonredundant` |
| Seeded-source sensitivity (supplement S5.5) | `explore_seedsource.py` | `20260817-seedsource` |
| Compositional vs count, and the calibrated diagnostic | `explore_countonly.py` | `20260815-countonly` |
| Packetization falsification | `explore_packetization.py` | `20260815-packetization` |
| Carrier-channel intervention | `explore_carrier_channel.py` | `20260815-carrier-channel` |
| Activation-regime comparison | `explore_endogenous.py` | `20260731-endogenous` |
| Throughput matching | `explore_rate_matched.py` | `20260815-rate-matched` |
| Tie-strength normalization | `explore_tiestrength_matched.py` | `20260815-tiestrength-matched` |
| Advocates, and robustness across topology and size | `explore_changeagent.py`, `explore_changeagent_robust.py` | `20260814-changeagent`, `20260815-changeagent-robust` |
| Capacity, threshold, density, stabilization sweeps | `exploratory/explore_comments.py` | `20260730-102229-comments` |
| Canonical staged sweep | `run.py` | `20260730-093338-full` |

`results/20260814-contagion-contrast/` holds an experiment that failed. It is not used in the article and its `NEGATIVE_RESULT.md` explains why. It is included because omitting it would misrepresent the record.

---

## Reproducing a result from scratch

Every run is seeded by replication index and is deterministic. Re-running the canonical sweep reproduces an identical MD5 over the full history.

```bash
ABM_REPS=200 python explore_sourcenonredundant.py compositional
ABM_REPS=200 python explore_sourcenonredundant.py source
ABM_REPS=200 python explore_sourcenonredundant.py count
```

Each writes a new timestamped directory under `results/`. To compare against the stored output, point the relevant entry in `verify_reported_values.py` at the new directory. The three-arm experiment is 4,800 runs and takes roughly 45 minutes on a laptop; the canonical sweep (10,800 runs) takes several hours.

Replication counts are set by `ABM_REPS`. **The engine default is 30 and no reported result uses it**; every reported cell is 200.

---

## Notes for anyone checking the model

- The focal specification holds contacts fixed at one per agent per tick. What the experiments vary is `transmission_prob`, the probability that a selected element transfers given a contact. "Flow" in the article means this, not contact frequency.
- Agent holdings in the main engine are a set of element types, so an agent cannot hold two tokens of the same type. Only `token_model.py` permits duplicates, which is what makes the equal-count comparator a genuine departure.
- Updating is asynchronous: agents act in a fresh random order each tick, not in lockstep.
- Runs stop at `run_length` or at quiescence, whichever comes first, at a mean of about tick 366 in the focal specification. Measuring at a fixed final tick instead lands at an arbitrary point of the recurring trigger cycle and will not reproduce the reported endpoints.
- The default eviction rule is uniformly random. A value-weighted rule that protected near-complete configurations would build the compositional result into the eviction mechanism rather than deriving it.

---

## Environment

Python 3.9.6. `requirements.txt` gives minimum versions; `requirements-lock.txt` pins the exact versions used to produce the reported output. The model itself needs only the standard library and NumPy. NetworkX is used for network construction, matplotlib for figures, pytest for tests, and FastAPI and uvicorn only for the optional viewer.

## Licence

MIT, see `LICENSE`.
