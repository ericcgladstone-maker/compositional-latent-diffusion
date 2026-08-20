#!/usr/bin/env python3
"""Replace the figure bitmaps inside the docx with the regenerated 200-rep ones.

The images are swapped by overwriting the bytes of the existing `word/media/*.png`
parts. Every relationship id, drawing element, size and caption stays exactly as
it is, so nothing about the document's structure or its 80 comments is touched.

The media part for each figure was identified by walking document.xml in order
and recording the paragraph each image follows. That mapping is recorded below
rather than recomputed, and `--check` re-derives it and refuses to run if the
document order has changed.

Usage:
  python swap_docx_images.py            # preview
  python swap_docx_images.py apply
"""
import glob, os, shutil, sys, zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
FIGDIR = os.path.join(RESULTS, "figures-200rep")

# Each figure is identified by the paragraph it follows, NOT by its media part
# name. Google Docs renumbers word/media/imageN.png wholesale on every round trip
# through the cloud copy, so a map keyed on part names goes stale the moment Eric
# edits a comment. The anchor text is stable; the part name is not.
MAP = [
    ("Limited attention.",                        (FIGDIR, "V1.png")),
    ("Observability gap.",                        ("*-wedge-explore", "fig_observability_gap.png")),
    ("Add-on: stabilization.",                    (FIGDIR, "V2-stabilization.png")),
    ("Add-on: enhanced transmission.",            (FIGDIR, "V2-enhanced.png")),
    ("Add-on: tie strength channels.",            (FIGDIR, "V2-tiestrength.png")),
    ("Add-on: internal coupling.",                (FIGDIR, "V2-internal-coupling.png")),
    ("Add-on: neighbor coupling.",                (FIGDIR, "V2-neighbor-coupling.png")),
    # relocated 2026-07-30 from the end of the document by move_collapse_figure.py
    ("Three contributions to the adoption gap",   ("*-wedge-explore", "fig_collapse.png")),
    ("Bistability under reversible",              ("*-tipping", "fig_bistability.png")),
    ("Source of the bistability.",                ("*-confirm", "fig_assembly_difficulty.png")),
    ("Capacity transition and the needed",        ("*-comments", "fig_w1_capacity_ratio.png")),
    ("Stabilization and enhanced transmission, crossed.", ("*-comments", "fig_w2_stab_enh.png")),
    ("Competitive ecology and the recruitment",   ("*-comments2", "fig_w5_ecology.png")),
    ("Recruitment-retention with member-gated",   (FIGDIR, "fig_w5c_inverted_u.png")),
    ("Triggering regime and the shape of adoption", (FIGDIR, "fig_endogenous_trigger.png")),
    ("Change agents and the size of the seeded minority", (FIGDIR, "fig_changeagent.png")),
    ("Transmissibility and the amount transmitted", (FIGDIR, "fig_rate_matched.png")),
]


def resolve(spec):
    base, name = spec
    if os.path.isabs(base):
        return os.path.join(base, name)
    ds = sorted(glob.glob(os.path.join(RESULTS, base)))
    return os.path.join(ds[-1], name) if ds else None


def doc_order(path):
    """(media part, preceding paragraph text) for each inline image, in order."""
    z = zipfile.ZipFile(path)
    rels = {r.get("Id"): r.get("Target")
            for r in ET.fromstring(z.read("word/_rels/document.xml.rels"))}
    body = ET.fromstring(z.read("word/document.xml")).find(f"{W}body")
    out, last = [], ""
    for child in body:
        if child.tag != f"{W}p":
            continue
        blips = list(child.iter(f"{A}blip"))
        txt = "".join(t.text or "" for t in child.iter(f"{W}t")).strip()
        if blips:
            for b in blips:
                out.append((os.path.basename(rels.get(b.get(f"{R}embed"), "?")), last))
        elif txt:
            last = txt
    return out


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    order = doc_order(DOCX)

    if len(order) != len(MAP):
        sys.exit(f"document has {len(order)} images but the map has {len(MAP)}; "
                 "the mapping is stale, re-derive before running")

    print("matching figures to media parts by the paragraph each follows:")
    bad = 0
    resolved = []          # (media part, source spec) in document order
    for (media, prev), (m_prev, spec) in zip(order, MAP):
        ok = prev.startswith(m_prev)
        if not ok:
            bad += 1
        resolved.append((media, spec))
        print(f"  {'ok ' if ok else 'NO '} {media:14s} follows {prev[:58]!r}")
    if bad:
        sys.exit(f"{bad} figures are not where the mapping says; refusing to swap")

    print("\nsources:")
    repl = {}
    missing = 0
    z = zipfile.ZipFile(DOCX)
    for media, spec in resolved:
        src = resolve(spec)
        ok = src and os.path.exists(src)
        if not ok:
            missing += 1
            print(f"  !! {media:14s} <- MISSING {spec}")
            continue
        old = z.getinfo("word/media/" + media).file_size
        new = os.path.getsize(src)
        repl["word/media/" + media] = src
        print(f"  ok {media:14s} <- {os.path.relpath(src, HERE)}  ({old} -> {new} bytes)")
    z.close()
    if missing:
        sys.exit(f"{missing} figures missing; run regen_figures.py first")

    if not apply:
        print(f"\n{len(repl)} images would be replaced (preview only).")
        return

    bak = DOCX + ".bak10"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")

    tmp = DOCX + ".tmp"
    zin = zipfile.ZipFile(DOCX)
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = (open(repl[item.filename], "rb").read()
                    if item.filename in repl else zin.read(item.filename))
            zout.writestr(item, data)
    zin.close()
    os.replace(tmp, DOCX)
    print(f"replaced {len(repl)} images in {os.path.basename(DOCX)}")


if __name__ == "__main__":
    main()
