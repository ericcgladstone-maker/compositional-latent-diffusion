#!/usr/bin/env python3
"""Merge the per-loss W5c shards into one result dir, verifying as it merges.

W5c was sharded by loss level to run on several cores (ABM_LOSSES). Each cell's
replications are seeded 0..REPS-1 independently of which other cells share the
process, so concatenating the shards is identical to one serial pass. This script
does not take that on faith: it re-derives every aggregate cell from the per-rep
raw rows and refuses to write a merged result if any cell disagrees, is missing,
or is duplicated.

Usage: python merge_w5c_shards.py <shard_dir> [<shard_dir> ...] [--out NAME]
"""
import csv, os, statistics as st, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")

LOSSES = [0.0, 0.001, 0.002, 0.004, 0.006, 0.01]
BETAS = [0.2, 0.5, 0.8]
ALPHAS = [0.0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0]
KEY = ("loss_rate", "beta_compression", "alpha_compression")


def fkey(r):
    return tuple(round(float(r[k]), 6) for k in KEY)


def main():
    out_name = None
    args, rest = [], list(sys.argv[1:])
    while rest:
        a = rest.pop(0)
        if a == "--out":
            if not rest:
                sys.exit("--out needs a value")
            out_name = rest.pop(0)
        elif a.startswith("--"):
            sys.exit(f"unknown option {a}")
        else:
            args.append(a)
    if out_name is None:
        # date-stamp the default so the doc's provenance line reads like every
        # other sweep citation (YYYYMMDD-...) rather than a bare name
        stamp = os.path.basename(args[0].rstrip("/"))[:8] if args else ""
        out_name = (stamp + "-merged-comments4") if stamp.isdigit() else "merged-comments4"
    # accept an absolute path, a path relative to cwd, or a bare dir name under results/
    dirs = []
    for d in args:
        for cand in (d, os.path.join(RESULTS, d)):
            if os.path.isdir(cand):
                dirs.append(os.path.abspath(cand))
                break
        else:
            sys.exit(f"no such shard dir: {d}")
    if not dirs:
        sys.exit("give at least one shard dir")

    agg, raw = [], []
    for d in dirs:
        a = os.path.join(d, "w5c_member_gated.csv")
        r = os.path.join(d, "w5c_member_gated_raw.csv")
        for path in (a, r):
            if not os.path.exists(path):
                sys.exit(f"missing {path} (shard incomplete)")
        agg += list(csv.DictReader(open(a)))
        raw += list(csv.DictReader(open(r)))
        print(f"  {os.path.basename(d):32s} agg={len(list(csv.DictReader(open(a))))} raw={len(list(csv.DictReader(open(r))))}")

    fails = []

    # --- completeness: every (loss, beta, alpha) exactly once -------------
    seen = defaultdict(int)
    for r in agg:
        seen[fkey(r)] += 1
    expected = {(round(l, 6), round(b, 6), round(a, 6))
                for l in LOSSES for b in BETAS for a in ALPHAS}
    missing = expected - set(seen)
    dupes = {k for k, v in seen.items() if v > 1}
    extra = set(seen) - expected
    print(f"\ncells: {len(seen)} unique of {len(expected)} expected")
    if missing:
        fails.append(f"{len(missing)} missing cells, e.g. {sorted(missing)[:3]}")
    if dupes:
        fails.append(f"{len(dupes)} duplicated cells, e.g. {sorted(dupes)[:3]}")
    if extra:
        fails.append(f"{len(extra)} unexpected cells, e.g. {sorted(extra)[:3]}")

    # --- re-derive every aggregate from the per-rep raw -------------------
    byraw = defaultdict(list)
    for r in raw:
        byraw[fkey(r)].append(float(r["alpha_share"]))
    reps = {len(v) for v in byraw.values()}
    print(f"raw rows: {len(raw)}   replications per cell: {sorted(reps)}")
    if len(reps) != 1:
        fails.append(f"uneven replication counts across cells: {sorted(reps)}")
    bad = 0
    for r in agg:
        k = fkey(r)
        if k not in byraw:
            bad += 1
            continue
        mine = round(st.mean(byraw[k]), 4)
        if abs(mine - float(r["alpha_share"])) > 1e-4:
            bad += 1
            print(f"  MISMATCH {k}: csv={r['alpha_share']} re-derived={mine}")
    print(f"aggregate cells re-derived from raw: {len(agg) - bad}/{len(agg)} match")
    if bad:
        fails.append(f"{bad} aggregate cells do not re-derive from raw")

    if fails:
        print("\nREFUSING TO WRITE MERGED RESULT:")
        for f in fails:
            print("  FAIL " + f)
        sys.exit(1)

    # --- write merged dir -------------------------------------------------
    out = os.path.join(RESULTS, out_name)
    os.makedirs(out, exist_ok=True)
    agg.sort(key=lambda r: (float(r["loss_rate"]), float(r["beta_compression"]),
                            float(r["alpha_compression"])))
    raw.sort(key=lambda r: (float(r["loss_rate"]), float(r["beta_compression"]),
                            float(r["alpha_compression"]), int(r["rep"])))
    for name, rows in (("w5c_member_gated.csv", agg), ("w5c_member_gated_raw.csv", raw)):
        with open(os.path.join(out, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)

    # --- recompute the interior-optimum summary over the FULL grid --------
    lines = []
    n_reps = sorted(reps)[0]
    lines.append(f"# W5c member-gated recruitment ecology  ({n_reps} reps, merged from "
                 f"{len(dirs)} per-loss shards)")
    lines.append(f"shards: {', '.join(os.path.basename(d) for d in dirs)}")
    lines.append("verified: every cell present exactly once; every aggregate re-derived "
                 "from per-rep raw")
    n_interior = 0
    for l in LOSSES:
        lines.append(f"\n## loss_rate = {l}")
        for b in BETAS:
            curve = []
            for a in ALPHAS:
                row = next(r for r in agg if fkey(r) == (round(l, 6), round(b, 6), round(a, 6)))
                curve.append((a, float(row["alpha_share"])))
            best = max(curve, key=lambda t: t[1])
            interior = 0.0 < best[0] < 1.0
            n_interior += interior
            lines.append(f"  rival={b}: " + "  ".join(f"a{p}={v}" for p, v in curve) +
                         f"   best={best[0]} (share {round(best[1], 4)}) "
                         f"{'INTERIOR (inverted-U)' if interior else 'edge'}")
    lines.append(f"\nINTERIOR OPTIMA (inverted-U cells): {n_interior} of "
                 f"{len(LOSSES) * len(BETAS)}")
    lines.append("DONE.")
    with open(os.path.join(out, "LOG.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-22:]))
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
