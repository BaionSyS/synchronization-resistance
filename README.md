# Synchronization Resistance: Measuring Multi-LLM Agreement Difficulty

A pre-registered five-hypothesis validation study of **Synchronization Resistance (SR)** — a per-prompt scalar, derived from the Kuramoto order parameter R(K) over a coupling sweep, that measures how hard it is to make a population of language models agree on a question.

**Scorecard: 3 pass · 1 inconclusive · 1 fail.** We publish the failure with the passes.

| Hypothesis | Result | Key metric |
|---|---|---|
| H1 — SR tracks human intuition | **INCONCLUSIVE** | ρ=0.30 (p=0.26), exactly on the pre-registered boundary |
| H2 — R(K) curves are classifiable | PASS | 18/20 at R²>0.90 |
| H3 — Two-point shortcut | PASS | MAE=0.04 vs full 11-point sweep |
| H4 — Replication stability | PASS | 0/4 status flips |
| H5 — Category discrimination | **FAIL** | JT p=0.06; predicted ordering violated (Creative > Controversial) |

The headline finding is the failure: human categorical labels (factual / creative / controversial / speculative) do **not** segment LLM disagreement. A category containing both SR=0.00 and SR=2.00 prompts cannot route anything. The instrument crosscuts human intuition — which is either its value or its problem. That's what we want argued about.

## Read it

- **Paper (v0.2.4):** [`paper/`](paper/) in this repo · DOI [10.5281/zenodo.20495904](https://doi.org/10.5281/zenodo.20495904)
- **All versions:** concept DOI [10.5281/zenodo.19953731](https://doi.org/10.5281/zenodo.19953731)
- **Pre-registration & results (before any data collection):** OSF registration [xqy5w](https://doi.org/10.17605/OSF.IO/XQY5W) (framework, 2026-03-17) · OSF project [xv9j6](https://doi.org/10.17605/OSF.IO/XV9J6) (Battery 3C hypotheses, deposited 2026-04-07, pre-data)

## Setup in one paragraph

Six local models (mistral 7B, gemma3 12B, glm4-flash, jamba-reasoning, phi4, qwen2.5 32B) via Ollama at temperature zero, 22 prompts committed at pre-registration, an 11-point coupling sweep K ∈ {0.0 … 1.0}. R₀ = baseline agreement at K=0; α = dR/dK = coupling susceptibility; SR = (τ−R₀)/α, capped at SR_MAX=2.0, with τ=0.70 fixed pre-data. Full definitions in the paper §3, methods §4.

## We want critique

This was built by a solo operator + AI collaborators, outside academia, on pre-registration discipline instead of institutional review. That means it has **not** been peer reviewed — you are the peer review. If the math is misapplied, the stats are underpowered, the Kuramoto framing is decoration, or the claims outrun the evidence — [open an issue](../../issues) or say it in [Discussions](../../discussions). Direct is better than polite.

## License

Paper text: CC BY-NC-ND 4.0. Patent and trademark rights are not licensed under the CC license (CC BY-NC-ND 4.0 §2(b)(2)); methods described may be subject to pending or issued patents held by BAION Systems LLC or Steven A. Mullins Jr.

## Cite

> Mullins Jr., S. A. (2026). *Synchronization Resistance: Measuring Multi-LLM Agreement Difficulty: A pre-registered five-hypothesis study (Battery 3C)*. Zenodo. https://doi.org/10.5281/zenodo.19953731
