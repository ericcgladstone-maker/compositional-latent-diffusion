# Replication materials

### Diffusion Before Adoption: A Model of Compositional Latent Diffusion

Model engine, experiment scripts, analysis and figure code, per-replication output for every reported cell, and an environment specification.

Eric Gladstone and Matthew E. Brashears. Working manuscript, in preparation for *Sociological Science*: https://graystoneindustries.co/research/#diffusion-before-adoption-a-model-of-compositional-latent-diffusion

This release (`v1.3.0-round4`) matches the Round 4 working manuscript of October 2026. The August 2026 submission version is tagged `v1.2.0-submission` and archived on OSF at https://doi.org/10.17605/OSF.IO/GFJ45.

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
| `make_manuscript_figures.py` | Original figure generator. Regenerates every figure in the article and its data audit. |
| `make_revised_figures.py` | Revised Figures 2, 4 and 5. Writes vector PDF and 600 dpi PNG to `results/figures-revised/`. Reads stored output only; recomputes nothing. |
| `emit_final_figures.py` | Emits the August 2026 main-text figure set (Figures 2-5) to `results/figures-final/` at publication spec. |
| `make_round3_figures.py` | The current main-text figures (Figures 1-5). Writes vector PDF and 600 dpi PNG to `results/figures-round3/`. Reads stored output only; recomputes nothing. |
| `tools/` | Document formatting and rendering scripts used to typeset the submission files. Like `docx_tooling/`, they operate on documents not distributed here. |
| `results/` | Per-replication output for every reported cell. See `results/README.md` for which sweeps are canonical. |
| `tests/` | 25 structural tests. |
| `viewer/`, `abm/server.py` | Optional live viewer. Not needed for replication. |
| `docx_tooling/` | Scripts that folded results into the authors' private working document. Included for transparency about how numbers reached the write-up. They operate on a document not distributed here and will not run. |
| `exploratory/` | Superseded exploratory scripts from the build phase. Retained so the record is complete; none produces a reported result. |

---

## Verification

Six independent checks. All should pass on a clean checkout.

| Command | What it establishes |
|---|---|
| `python verify_reported_values.py` | Every value in the article matches stored output. 97 checks. |
| `python -m pytest -q` | Structural correctness of network construction, requirement sets, capacity accounting, metrics. 25 tests. |
| `python verify_mechanisms.py` | Each optional mechanism does what it is documented to do, and nothing when off. 39 assertions. |
| `python verify_noop.py` | Every additive engine change is byte-identical to the prior model when disabled. 18 paths. |
| `python verify_token_arms.py` | The three readiness arms share one token history at every tick, including component and sender labels. 9,030 checks. |
| `python verify_token_activation_invariance.py` | The three-arm result is identical under scheduled and immediate activation, replication by replication, and the scheduled arm reproduces the canonical output. Added in Round 4. |

`verify_token_arms.py` is the load-bearing check for the article's identification claim: if the arms ever diverge in what they hold, the comparison is between different worlds.

`verify_reported_values.py` checks the 97 values of the August 2026 version. The values added in Round 4, from the immediate-manifestation runs, are recorded in the `LOG` files and CSVs of the three `results/20261006-*` directories and are not yet part of that script.

---

## Where each result comes from

Main-text figures and the code and data behind them. The current manuscript uses the Round 3 figure set; the generators named below for the August 2026 version are retained.

| Article element | Produced by | Data |
|---|---|---|
| Figure 1, conceptual architecture | `make_round3_figures.py::figure1` | none, schematic |
| Figure 2, elements before adoption | `make_round3_figures.py::figure2` | `results/20260731-endogenous/`, `results/20260816-carrier-diagnostics/`, `results/20260816-carrier-diagnostics-endo/` |
| Figure 3, retention and conversion | `make_round3_figures.py::figure3` | `results/20260730-102229-comments/` |
| Figure 4, element identity | `make_round3_figures.py::figure4` | `results/20260816-sourcenonredundant/` |
| Figure 5, post-manifest retention | `make_round3_figures.py::figure5` | `results/20260730-093338-full/`, `results/20260730-102229-comments/` |

August 2026 submission version:

| Article element | Produced by | Data |
|---|---|---|
| Figure 1, conceptual architecture | `make_manuscript_figures.py::figure1` | none, schematic |
| Figure 2, propagation before manifestation | `make_revised_figures.py::figure2` | `results/20260731-endogenous/`, `results/20260816-carrier-diagnostics-endo/` |
| Figure 3, retention governs conversion | `make_manuscript_figures.py::figure3` | `results/20260730-102229-comments/` |

Figure 3's white markers are labelled "interpolated capacity at mean object-specific adoption = 0.50". The plotted quantity is `final_manifest_share`, which is the mean across objects of the share of agents manifesting that object, **not** the share of agents manifesting at least one object. Those are different quantities: at the focal specification they are 0.6482 and 0.9217 respectively. See "Notes for anyone checking the model" below.
| Figure 4, content identity vs source diversity | `make_revised_figures.py::figure4` | `results/20260816-sourcenonredundant/` |
| Figure 5, retention and the return to transmission | `make_revised_figures.py::figure5` | `results/20260730-102229-comments/`, `results/20260730-093338-full/` |
| Figure S1, carrier threshold sensitivity | `make_manuscript_figures.py::figureS_carriers` | both `carrier-diagnostics` directories |
| Figure S2, manifest advocates | `make_manuscript_figures.py::figureS_advocates` | `results/20260814-changeagent/` |
| Table 1 | conceptual, no data | none |
| Table 2, empirical diagnostics | conceptual, no data | none |

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
| Immediate manifestation upon readiness (Round 4) | `ABM_PARTS=2imme python explore_endogenous.py`; `ABM_TRIGGER=immediate python explore_carrier_diagnostics.py` | `20261006-immediate-capacity`, `20261006-carrier-diagnostics-immediate` |
| Three-arm invariance to the activation rule (Round 4) | `verify_token_activation_invariance.py` | `20261006-token-activation-invariance` |
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
- `manifest_share` is `sum(len(a.manifest) for a in agents) / (n * n_objects)`: the share of
  (agent, object) cells in the manifest state, equivalently the mean across objects of
  per-object adoption. `final_manifest_share`, `peak_manifest_share` and the token model's
  `adoption` are the same construct. The separate `manifest_any` in
  `explore_carrier_diagnostics.py` is the union -- agents manifesting at least one object --
  and is larger.
- Sender state in `_record_transfer` is classified with `any(bid in sender.manifest for bid
  in owners)`: a sender counts as manifest when it manifests **at least one** object served
  by the transferred component. This matters only for the single component the two objects
  share. The counters run after a successful transfer, draw no random numbers and change no
  state.
- The default eviction rule is uniformly random. A value-weighted rule that protected near-complete configurations would build the compositional result into the eviction mechanism rather than deriving it.

---

## Environment

Python 3.9.6. `requirements.txt` gives minimum versions; `requirements-lock.txt` pins the exact versions used to produce the reported output. The model itself needs only the standard library and NumPy. NetworkX is used for network construction, matplotlib for figures, pytest for tests, and FastAPI and uvicorn only for the optional viewer.

## Licence

MIT, see `LICENSE`.
