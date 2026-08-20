#!/usr/bin/env python3
"""Single entrypoint for the latent-adoption ABM.

  python run.py viewer                 # launch the live HTML viewer
  python run.py sweep --phase V1       # one phase's focal sweep
  python run.py sweep --full           # the whole V0 -> end path
  python run.py single --phase V1      # run one phase once, print the summary
  python run.py check                  # quick sanity gates (V0 saturates, V1 doesn't)

The viewer and the sweeps run the same engine (abm/model.py).
"""

import argparse
import sys

from abm import config as C
from abm import phases as P


def cmd_viewer(args):
    from abm import server
    print(f"Viewer on http://{args.host}:{args.port}  (Ctrl-C to stop)")
    server.serve(args.host, args.port)


def _bar(done, total, message):
    width = 30
    filled = int(width * done / max(1, total))
    sys.stdout.write(f"\r[{'#' * filled}{'.' * (width - filled)}] {done}/{total}  {message[:48]:48}")
    sys.stdout.flush()
    if done == total:
        sys.stdout.write("\n")


def cmd_sweep(args):
    from abm import sweep
    if args.full:
        outdir = sweep.run_full_sweep(replications=args.reps, base_seed=args.seed,
                                      with_invariants=args.invariants, progress=_bar)
    else:
        if not args.phase:
            sys.exit("specify --phase <id> or --full")
        outdir = sweep.run_sweep([args.phase], replications=args.reps, base_seed=args.seed,
                                 with_invariants=args.invariants, progress=_bar)
    print(f"\nResults written to: {outdir}")


def cmd_single(args):
    from abm.model import World
    cfg = (P.config_for_phase(args.phase) if args.phase else C.default_config())
    if args.seed is not None:
        cfg["seed"] = args.seed
    w = World(cfg)
    w.run()
    from abm.sweep import summarize_history
    summary = summarize_history(w.history, [b.label for b in w.big_things])
    print(f"phase={args.phase or 'defaults'}  seed={cfg['seed']}")
    for k, v in summary.items():
        print(f"  {k:34} {v}")


def cmd_check(args):
    from abm.model import World
    from abm import invariants

    print("V0 (should saturate): ", end="")
    w0 = World(P.config_for_phase("V0", {"seed": 1, "run_length": 600}))
    invariants.run_with_checks(w0)
    ms0 = w0.history[-1]["manifest_share"]
    print(f"manifest_share={ms0:.3f}  {'OK' if ms0 > 0.95 else 'LOW (check seeding/density)'}")

    print("V1 (should NOT saturate): ", end="")
    w1 = World(P.config_for_phase("V1", {"seed": 1, "run_length": 1500}))
    invariants.run_with_checks(w1)
    ms1 = w1.history[-1]["manifest_share"]
    print(f"manifest_share={ms1:.3f}  {'OK (constrained)' if ms1 < ms0 else 'check capacity'}")

    print("Invariants held across both runs.")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("viewer", help="launch the live viewer")
    v.add_argument("--host", default="127.0.0.1")
    v.add_argument("--port", type=int, default=8000)
    v.set_defaults(func=cmd_viewer)

    s = sub.add_parser("sweep", help="headless batch sweep")
    s.add_argument("--phase", help="phase id (see phases.py)")
    s.add_argument("--full", action="store_true", help="run every phase in order")
    s.add_argument("--reps", type=int, default=None, help="replications per cell")
    s.add_argument("--seed", type=int, default=0)
    s.add_argument("--invariants", action="store_true", help="assert invariants each run")
    s.set_defaults(func=cmd_sweep)

    o = sub.add_parser("single", help="run one config once and print the summary")
    o.add_argument("--phase", help="phase id")
    o.add_argument("--seed", type=int, default=None)
    o.set_defaults(func=cmd_single)

    c = sub.add_parser("check", help="quick sanity gates")
    c.set_defaults(func=cmd_check)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
