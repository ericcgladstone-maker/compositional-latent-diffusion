#!/usr/bin/env python3
"""Move the wedge-collapse figure next to the paragraph it illustrates.

The figure showing the adoption gap under successive removal of the three
barriers sits at the very end of the document, after "New specification
details", rather than after "Three contributions to the adoption gap". The fold
that introduced it intended it for the synthesis, so this looks like an append
that never got relocated.

The move is a pure reordering of one paragraph element. No text, run, image,
relationship or comment is touched, and the checks below assert that.

Usage:
  python move_collapse_figure.py           # preview
  python move_collapse_figure.py apply
"""
import os, shutil, sys, zipfile

import docx
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))

ANCHOR = "Three contributions to the adoption gap"
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def fingerprint(path):
    z = zipfile.ZipFile(path)
    n = z.namelist()
    dx = z.read("word/document.xml").decode("utf8")
    return {
        "parts": len(n),
        "media": len([x for x in n if x.startswith("word/media/")]),
        "comments": z.read("word/comments.xml").decode("utf8").count("<w:comment "),
        "commentRefs": dx.count("commentReference"),
        "images": dx.count("<a:blip") + dx.count(f"<{A_NS}blip"),
        "tables": dx.count("<w:tbl>"),
        "paragraphs": dx.count("<w:p>") + dx.count("<w:p "),
    }


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    doc = docx.Document(DOCX)

    # `doc.paragraphs` rebuilds its objects on every access, so take it once
    paras = list(doc.paragraphs)

    imgs = [p for p in paras if list(p._p.iter(f"{A_NS}blip"))]
    if not imgs:
        sys.exit("no inline images found")
    fig_p = imgs[-1]          # the trailing figure is the one to relocate
    if fig_p.text.strip():
        sys.exit("the trailing image paragraph also carries text; not moving it")

    anchors = [p for p in paras if p.text.strip().startswith(ANCHOR)]
    if len(anchors) != 1:
        sys.exit(f"anchor paragraph matched {len(anchors)} times, expected 1")
    anchor = anchors[0]

    body = list(doc.element.body)
    i_fig, i_anchor = body.index(fig_p._p), body.index(anchor._p)
    following = paras[paras.index(anchor) + 1]
    print(f"figure is body element {i_fig} of {len(body)} (last content element: "
          f"{i_fig >= len(body) - 2})")
    print(f"anchor  is body element {i_anchor}: {anchor.text.strip()[:70]}")
    print(f"it would move to sit directly after that anchor, before: "
          f"{following.text.strip()[:70]!r}")

    if not apply:
        print("\npreview only, nothing written.")
        return

    before = fingerprint(DOCX)
    bak = DOCX + ".bak11"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"backup -> {os.path.basename(bak)}")

    anchor._p.addnext(fig_p._p)
    doc.save(DOCX)

    after = fingerprint(DOCX)
    print("\nfingerprint before/after:")
    bad = 0
    for k in before:
        same = before[k] == after[k]
        bad += (not same)
        print(f"  {k:12s} {before[k]:5d} -> {after[k]:5d}{'' if same else '  <-- CHANGED'}")
    if bad:
        shutil.copy2(bak, DOCX)
        sys.exit(f"{bad} structural differences; RESTORED from backup")

    d2 = docx.Document(DOCX)
    order = [p for p in d2.paragraphs if list(p._p.iter(f"{A_NS}blip"))]
    body2 = list(d2.element.body)
    ia = body2.index([p for p in d2.paragraphs
                      if p.text.strip().startswith(ANCHOR)][0]._p)
    print(f"\nfigure now sits at body element {body2.index(order[-1]._p) if False else ''}"
          f"{[body2.index(p._p) for p in order]}")
    print(f"anchor at {ia}; figure immediately after: "
          f"{ia + 1 in [body2.index(p._p) for p in order]}")
    print("moved.")


if __name__ == "__main__":
    main()
