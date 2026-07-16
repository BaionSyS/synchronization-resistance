# Reproducing the results

Every number in the paper is derived from the files in this repository. You do not
need our engine, an API key, a GPU, or Ollama to check them.

```bash
pip install numpy scipy
python3 analysis/reproduce.py
```

Expected output:

```
=== Battery 3C H1-H5 re-derivation (raw gates, frozen SR funcs) ===

H1: rho=0.300 p=0.258   (v0.1.0: rho=0.30 p=0.26)  -> REPRODUCES
H2: 18/20 R^2>0.90 (rep1)   (v0.1.0: 18/20)
H3: MAE=0.0438   (v0.1.0: 0.07 -> CORRECTED to 0.04)
H4: 0/4 status flips   (v0.1.0: 0/4)
H5: F<C<X<S means=[0.0, 0.718, 0.392, 0.713] monotone=False   (v0.1.0: ordering violated, FAIL)
```

That is the whole scorecard: 3 pass, 1 inconclusive (H1), 1 fail (H5). It runs in a
few seconds.

## What is the reproduction boundary

**Read this before you conclude the study is independently reproduced. It is not.**

The study has two halves, and this repository publishes one of them.

| Step | What it does | Published here |
|---|---|---|
| 1. Measurement | Six local models answer 22 prompts; a coupling sweep over K produces the order parameter R(K) | **No** — the engine that ran it is unreleased |
| 2. Derivation | R(K) → SR → the five hypothesis tests | **Yes** — in full |

`data/k_sweep/` contains the R(K) measurements as they came out of step 1. They are
published as **inputs we are asking you to check, not outputs you can currently
regenerate**. If you think the measurement itself is wrong — that the coupling did
something other than what we say, or that R was computed incorrectly — this
repository cannot settle that for you, and we are not claiming it can.

What it does let you do is check the part where the paper's claims actually live:
whether SR is a coherent construct, whether the statistics support the conclusions,
whether n=22 is enough, whether the failure of H5 means what we say it means.

The coordination substrate that produced R(K) (U.S. Provisional Patent Application
#64/042,046) is unreleased pending counsel review. When that changes, step 1 becomes
reproducible too, and this section gets rewritten.

## What's in here

```
prompts/                        22 prompt packets, verbatim as pre-registered 2026-04-07
data/
  manifest.json                 peers, temperature, seed, K-points, pre-ranking source
  k_sweep/rep{1,2,3}/           726 gate files = 22 prompts x 11 K-points x 3 reps
  battery3_ksweep.csv           the same measurements, flattened to long format
analysis/
  synchronization_resistance.py the SR primitive (frozen 2026-04-06); imports numpy only
  reproduce.py                  the H1-H5 derivation
paper/                          the manuscript (byte-identical to the Zenodo deposit)
```

A gate file is the unit of measurement — one prompt, one K, one rep:

```json
{"decision":"BLOCK","diagnosis":"Multi-Dimension Divergence",
 "r_values":[0.600927,0.428662,0.949923],"thresholds":[0.85,0.7,0.6],
 "group_id":0,"tick":26,"member_count":6}
```

`r_values[0]` is the conclusion dimension — the one SR is computed on.

## Provenance

`analysis/reproduce.py` is the vault's own re-derivation receipt, written 2026-06-01 to
settle a discovered defect: the published H3 MAE was 0.07 and re-derivation from the raw
gates gave 0.04. The paper carries the correction, and this script is the artifact that
found it. It is published here unchanged except for six lines rebinding absolute paths to
repo-relative ones; a header comment in the file records the vault original's SHA-256 so
the two can be diffed.

`analysis/synchronization_resistance.py` is byte-identical to the frozen 2026-04-06 copy
the study ran against.

The measurements in `data/k_sweep/` were committed 2026-04-07, before analysis, per the
OSF pre-registration.

## Environment

Verified on Python 3.12.3, numpy 2.4.3, scipy 1.17.1. The derivation uses only
`polyfit`, `spearmanr`, and basic array math; it is not version-sensitive.

The original measurements were produced on an AMD Radeon PRO W7900 running six models
via Ollama at temperature 0. Per-run energy and hardware provenance are recorded in the
receipts.

## If you find something

Open an issue. A result that contradicts the paper is the most useful thing you can
send us — please include the command you ran and its full output.
