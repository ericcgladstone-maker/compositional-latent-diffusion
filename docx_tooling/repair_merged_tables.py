#!/usr/bin/env python3
"""Split follow-up tables that an editor save merged into the table above them.

Found 2026-10-06: the build docx saved on 2026-08-18 had four pairs of adjacent
tables joined into one (the second table's header row appearing as a data row of
the first). Values were intact, but the gate could no longer see the absorbed
tables and reported their rows as having no source. This splits each table at
any row that is itself a recognised follow-up header, and puts an empty paragraph
between the parts so they cannot merge again. Nothing else is changed.

  python repair_merged_tables.py           # preview
  python repair_merged_tables.py apply
"""
import copy, os, sys

import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import fold_200rep_tables as FT

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))


def split_points(tbl):
    rows = tbl.findall(qn("w:tr"))
    texts = [["".join(t.text or "" for t in tc.iter(qn("w:t"))).strip()
              for tc in tr.findall(qn("w:tc"))] for tr in rows]
    return [i for i, cells in enumerate(texts) if i > 0 and FT.identify(cells)], texts


def regrid(tbl):
    rows = tbl.findall(qn("w:tr"))
    ncol = max(len(tr.findall(qn("w:tc"))) for tr in rows)
    grid = tbl.find(qn("w:tblGrid"))
    old = grid.findall(qn("w:gridCol"))
    total = sum(int(g.get(qn("w:w"), "0")) for g in old) or 9000
    for g in old:
        grid.remove(g)
    for _ in range(ncol):
        g = OxmlElement("w:gridCol"); g.set(qn("w:w"), str(total // ncol)); grid.append(g)


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    doc = docx.Document(DOCX)
    n = 0
    for t in list(doc.tables):
        tbl = t._tbl
        cuts, texts = split_points(tbl)
        for cut in reversed(cuts):
            print(f"split: {FT.identify(texts[0])!r} | {FT.identify(texts[cut])!r} at row {cut}")
            n += 1
            if not apply:
                continue
            new = copy.deepcopy(tbl)
            for tr in new.findall(qn("w:tr"))[:cut]:
                new.remove(tr)
            for tr in tbl.findall(qn("w:tr"))[cut:]:
                tbl.remove(tr)
            regrid(new); regrid(tbl)
            spacer = OxmlElement("w:p")
            tbl.addnext(spacer)
            spacer.addnext(new)
    print(f"{n} merged table(s) {'split' if apply else 'found (preview only)'}")
    if apply and n:
        doc.save(DOCX)
        print("saved.")


if __name__ == "__main__":
    main()
