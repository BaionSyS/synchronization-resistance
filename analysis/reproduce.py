#!/usr/bin/env python3
# Battery 3C H1-H5 re-derivation — verify | reproducibility receipt for the H3 MAE retract-rewrite
# Spec: SCIENCE/BOUNCE/BATTERY_3C_SR_KSWEEP/BATTERY_3C_H1H5_RESULTS_v0.1.1 ; BUG_LEDGER/BOUNCE row B3C-MAE-1
# Backend: reads immutable raw gates bounce/results/BATTERY3/k_sweep/ via frozen synchronization_resistance.py
"""
Re-derives all five Battery 3C hypotheses from the immutable 2026-04-07 raw gate
files using the frozen canonical SR functions, to settle the 0.04-vs-0.07 H3 MAE
drift discovered 2026-06-01. Result: H1/H2/H4/H5 reproduce exactly; H3 MAE = 0.04
(0.044, 3-rep mean), NOT the v0.1.0-published 0.07. See spec Amendment Record.

WHY this lives in the vault (not /tmp): the defect being corrected is a
reproducibility gap; the fix must itself be reproducible. Run on the box that
has PROJ_CODE mounted: `python3 battery_3c_h1h5_rederivation_*.py`.
"""
import json, glob, os, sys
from collections import defaultdict
import numpy as np

# PUBLISHED COPY: the only change from the vault original is these six lines --
# absolute PROJ_CODE paths rebound to repo-relative ones. The derivation below is
# byte-identical. Vault original SHA-256:
#   0100ca71c7411042cafc35ed0ef0b2430e1fd4f1fce6371cf727f7f03c344910
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "analysis"))
from synchronization_resistance import compute_sr, two_point_sr  # frozen 2026-04-06

BASE = f"{REPO}/data/k_sweep"                       # immutable, committed 2026-04-07
MAN = json.load(open(f"{REPO}/data/manifest.json"))
cat = {p["id"]: p["category"] for p in MAN["prompts"]}
rank = {p["id"]: p.get("pre_rank") for p in MAN["prompts"]}

data = defaultdict(dict)  # (rep, prompt) -> {K: r_conclusion}
for rep in ("rep1", "rep2", "rep3"):
    for pdir in sorted(glob.glob(f"{BASE}/{rep}/*")):
        pid = os.path.basename(pdir)
        for gf in glob.glob(f"{pdir}/gate_K*.json"):
            K = float(os.path.basename(gf).replace("gate_K", "").replace(".json", ""))
            data[(rep, pid)][K] = json.load(open(gf))["r_values"][0]  # [0]=conclusion dim

prompts = sorted({p for (_, p) in data})
non_adv = [p for p in prompts if cat[p] in ("factual", "creative", "controversial", "speculative")]
set20 = [p for p in prompts if cat[p] in ("factual", "creative", "controversial", "speculative", "adversarial")]


def full(rep, pid):
    return compute_sr(sorted(data[(rep, pid)].items()), bootstrap=False)


def two(rep, pid):
    kr = data[(rep, pid)]
    return two_point_sr(kr[0.0], kr[0.5], 0.5)


def mean_sr(pid):
    return float(np.mean([full(r, pid)["SR"] for r in ("rep1", "rep2", "rep3") if (r, pid) in data]))


print("=== Battery 3C H1-H5 re-derivation (raw gates, frozen SR funcs) ===\n")

# H1 — Spearman pre_rank vs 3-rep-mean SR over 16 non-adv
from scipy import stats
rho, p = stats.spearmanr([rank[x] for x in non_adv], [mean_sr(x) for x in non_adv])
print(f"H1: rho={rho:.3f} p={p:.3f}   (v0.1.0: rho=0.30 p=0.26)  -> {'REPRODUCES' if abs(rho-0.30)<0.02 else 'DIFF'}")

# H2 — fraction with R^2>0.90 (constant => pass), rep1
npass = 0
for pid in set20:
    ks = np.array(sorted(data[("rep1", pid)])); rs = np.array([data[("rep1", pid)][k] for k in ks])
    if np.allclose(rs, rs[0]):
        r2 = 1.0
    else:
        c = np.polyfit(ks, rs, 1); pred = np.polyval(c, ks)
        r2 = 1 - np.sum((rs - pred) ** 2) / np.sum((rs - np.mean(rs)) ** 2)
    npass += r2 > 0.90
print(f"H2: {npass}/{len(set20)} R^2>0.90 (rep1)   (v0.1.0: 18/20)")

# H3 — two-point MAE, 3-rep mean over 20-set (the corrected figure)
perr = {p: abs(mean_sr(p) - np.mean([two(r, p) for r in ("rep1", "rep2", "rep3") if (r, p) in data])) for p in set20}
mae = float(np.mean(list(perr.values())))
worst = sorted(perr.items(), key=lambda kv: -kv[1])[:3]
print(f"H3: MAE={mae:.4f}   (v0.1.0: 0.07 -> CORRECTED to 0.04)   worst={[(p, round(e,3)) for p,e in worst]}")

# H4 — status flips across reps for the 4 designated prompts
flips = 0
for pid in ["F4_tides", "C1_card_game", "X3_mandatory_voting", "S3_mars_colony"]:
    sts = {full(r, pid)["status"] for r in ("rep1", "rep2", "rep3") if (r, pid) in data}
    flips += len(sts) > 1
print(f"H4: {flips}/4 status flips   (v0.1.0: 0/4)")

# H5 — category-mean ordering F<C<X<S
order = ["factual", "creative", "controversial", "speculative"]
means = [round(np.mean([mean_sr(p) for p in non_adv if cat[p] == c]), 3) for c in order]
mono = all(means[i] <= means[i + 1] for i in range(3))
print(f"H5: F<C<X<S means={means} monotone={mono}   (v0.1.0: ordering violated, FAIL)")
