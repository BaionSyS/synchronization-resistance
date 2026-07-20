# Data Correction SR-01 — A failed peer was replayed as a zero-phase oscillator

**Date:** 2026-07-20 (UTC) · **Scope:** 4 of 66 sweep series · **Disposition:** headline scorecard **preserved** — this is a measurement correction, **not** a retraction.

We found a data-integrity defect in the raw measurements this repository asks you to check, corrected it, and are documenting exactly what changed. The original (contaminated) values remain in this repo's git history; the corrected values are now the committed data.

---

## What was wrong

Each sweep ran six local models. In four series, one model — `glm4_flash` — **failed to respond** (empty output). The primary receipts recorded this correctly (`peers_responding: 5`, `peers_failed: 1`, `ok: false`).

The historical K-sweep replay script did not honor that flag. It iterated every round-0 peer and substituted a **zero** for each missing phase angle:

```python
pa = p.get('phase_angles', {})
theta1 = pa.get('conclusion', 0)   # failed peer -> 0, not dropped
theta2 = pa.get('basis', 0)
theta3 = pa.get('effort', 0)
```

The failed model was therefore deposited into the field as a **sixth oscillator pinned at angle 0** — a phantom "agreer at zero." The gate then reported `member_count: 6`. The Kuramoto order parameter R was computed over six oscillators, one of which was an artifact. Correct handling excludes the failed peer and computes R over the **five valid** responders.

## Which series

| Series | Peers responding | Failed peer |
|---|---|---|
| `rep1/A3_dynamic_range` | 5 / 6 | `glm4_flash` |
| `rep2/A3_dynamic_range` | 5 / 6 | `glm4_flash` |
| `rep3/A3_dynamic_range` | 5 / 6 | `glm4_flash` |
| `rep2/C3_blacksmith_hospital` | 5 / 6 | `glm4_flash` |

The other **62 series are unaffected** — all six models responded, so there was no phantom to remove; their gates are byte-for-byte unchanged.

## The disposition: the headline survives

Re-deriving all five hypotheses from the corrected data (same frozen `analysis/synchronization_resistance.py`, same `analysis/reproduce.py`):

| Hypothesis | Published | Corrected | Change |
|---|---|---|---|
| H1 — tracks human intuition | ρ = 0.30 (p = 0.26), **INCONCLUSIVE** | ρ = 0.300482 (p = 0.258134), **INCONCLUSIVE** | none (rounded) |
| H2 — curves classifiable | 18/20, **PASS** | 18/20, **PASS** | none |
| H3 — two-point shortcut | MAE = 0.0438, **PASS** | MAE = 0.0433, **PASS** | tighter |
| H4 — replication stability | 0/4 flips, **PASS** | 0/4 flips, **PASS** | none |
| H5 — category discrimination | ordering violated, **FAIL** | ordering violated, **FAIL** | none |

**No status flips. No headline reversal.** H3's mean absolute error actually improves slightly. The correction changes four curves; it does not change a single one of the study's five dispositions.

## How large were the changes

Maximum absolute per-point change in R across the 11-point sweep, per affected prompt and dimension:

| Prompt | Conclusion | Basis | Effort |
|---|---:|---:|---:|
| `A3_dynamic_range` | 0.020554 | 0.129827 | 0.277105 |
| `C3_blacksmith_hospital` | 0.057914 | 0.048698 | 0.115874 |

The phantom oscillator most affected the **effort** and **basis** dimensions (where the five real models were most spread), and least affected **conclusion** (where they already agreed). Example, `rep1/A3_dynamic_range` at K=0: `[0.581914, 0.046600, 0.568302]` → `[0.602392, 0.176427, 0.843711]`.

## How it was corrected

The correction was produced by the **same measurement pathway** that produced the originals — the real field engine and convergence gate, not a recomputation or a proxy — with one change: peers with `ok: false` are excluded before their phases are deposited, so only valid responders form the convergence set.

The correction was validated three ways before it was trusted:

1. **Reproduction.** Running the *unmodified* (6-peer) pathway reproduces the published gate values **byte-for-byte** — establishing that the pathway is faithful on this machine.
2. **Independent recompute.** At K=0 (no coupling), R is a closed-form Kuramoto order parameter; the corrected 5-peer values match a hand computation over the five stored phase angles exactly.
3. **Independent audit.** An external reviewer, given the measurement engine as a black box, ran the identical correction and reported the identical per-point deltas and corrected scorecard.

## What changed in this repository

- `data/k_sweep/{rep1,rep2,rep3}/A3_dynamic_range/gate_K*.json` and `data/k_sweep/rep2/C3_blacksmith_hospital/gate_K*.json` — corrected `r_values`, `member_count: 5`, updated `decision`/`diagnosis`.
- `data/battery3_ksweep.csv` — the 44 corresponding rows regenerated.
- `data/CORRECTION_SR-01.json` — machine-readable record of the defect, the affected series, the dropped peer, and per-point before/after values.
- The original contaminated values are preserved in this repository's git history.

## Reproduce it

```bash
pip install numpy scipy
python3 analysis/reproduce.py
```

prints the corrected scorecard above. As stated in [REPRODUCE.md](REPRODUCE.md), we publish the derivation (R(K) → SR → the five tests), not the substrate that produced R(K); that substrate is unreleased pending counsel review. This correction operates entirely on the published inputs — the corrected `r_values` are here for you to check exactly as the originals were.

---

*We publish the failure with the passes — and we publish our corrections the same way.*
