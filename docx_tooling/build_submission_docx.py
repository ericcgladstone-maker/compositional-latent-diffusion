#!/usr/bin/env python3
"""Assemble the blinded submission DOCX and the online-supplement DOCX.

Markdown is the working format for the manuscript, but the journal wants a
document. This converts it without a general-purpose markdown library, because
the mapping needed here is specific: figure captions live in a trailing section
of the markdown and have to be relocated inline at their first callout, the
literature table has to become a native Word table rather than an image, and the
whole thing has to come out blinded, 12pt, 1.5-spaced and page-numbered.

  python build_submission_docx.py
"""
import os, re, sys

import docx
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIGDIR = os.path.join(HERE, "results", "figures-manuscript")
OUTDIR = os.path.join(ROOT, "submission")
os.makedirs(OUTDIR, exist_ok=True)

BODY_FONT = "Cambria"          # readable serif available on macOS and Windows
BODY_PT = 12

FIG_FILES = {
    1: "figure1_architecture.png",
    2: "figure2_before_manifestation.png",
    3: "figure3_retention_conversion.png",
    4: "figure4_composition_vs_count.png",
    5: "figure5_retention_returns.png",
}


# ------------------------------------------------------------------ styling
def base_document():
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = BODY_FONT
    st.font.size = Pt(BODY_PT)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), BODY_FONT)
    pf = st.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(0)
    pf.space_before = Pt(0)
    for s in doc.sections:
        s.top_margin = s.bottom_margin = Inches(1)
        s.left_margin = s.right_margin = Inches(1)
    for name, size, bold, before, after in (
            ("Heading 1", 14, True, 18, 6),
            ("Heading 2", 12, True, 14, 4),
            ("Heading 3", 12, False, 12, 4)):
        h = doc.styles[name]
        h.font.name = BODY_FONT
        h.font.size = Pt(size)
        h.font.bold = bold
        h.font.italic = (name == "Heading 3")
        h.font.color.rgb = RGBColor(0, 0, 0)
        h.paragraph_format.space_before = Pt(before)
        h.paragraph_format.space_after = Pt(after)
        h.paragraph_format.keep_with_next = True
    return doc


def add_page_numbers(doc):
    for section in doc.sections:
        p = section.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        for instr, kind in (("begin", "fldChar"), ("PAGE", "instrText"),
                            ("end", "fldChar")):
            el = OxmlElement(f"w:{kind}")
            if kind == "fldChar":
                el.set(qn("w:fldCharType"), instr)
            else:
                el.set(qn("xml:space"), "preserve")
                el.text = " PAGE "
            run._r.append(el)
        run.font.name = BODY_FONT
        run.font.size = Pt(10)


def table_borders(tbl):
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{e}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), "808080")
        b.append(el)
    tbl._tbl.tblPr.append(b)


# ------------------------------------------------------------ inline markup
INLINE = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`)")


def add_runs(par, text, size=None):
    """Render **bold**, *italic* and `code` into a paragraph."""
    for chunk in INLINE.split(text):
        if not chunk:
            continue
        if chunk.startswith("**") and chunk.endswith("**"):
            r = par.add_run(chunk[2:-2]); r.bold = True
        elif chunk.startswith("`") and chunk.endswith("`"):
            r = par.add_run(chunk[1:-1]); r.name = "Consolas"
        elif chunk.startswith("*") and chunk.endswith("*"):
            r = par.add_run(chunk[1:-1]); r.italic = True
        else:
            r = par.add_run(chunk)
        r.font.name = BODY_FONT
        if size:
            r.font.size = Pt(size)
    return par


def para(doc, text, size=None, italic_all=False, space_after=6, align=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    if align is not None:
        p.alignment = align
    add_runs(p, text, size)
    if italic_all:
        for r in p.runs:
            r.italic = True
    return p


def md_table(doc, rows):
    hdr = [c.strip() for c in rows[0].strip("|").split("|")]
    body = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
    t = doc.add_table(rows=1, cols=len(hdr))
    table_borders(t)
    for j, h in enumerate(hdr):
        cell = t.rows[0].cells[j]
        cell.paragraphs[0].paragraph_format.space_after = Pt(2)
        add_runs(cell.paragraphs[0], f"**{h}**", size=9)
    for row in body:
        cells = t.add_row().cells
        for j, v in enumerate(row[:len(hdr)]):
            cells[j].paragraphs[0].paragraph_format.space_after = Pt(2)
            add_runs(cells[j].paragraphs[0], v, size=9)
    return t


def add_figure(doc, n, caption, width=6.3):
    path = os.path.join(FIGDIR, FIG_FILES[n])
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(path, width=Inches(width))
    # caption is a separate, editable Word paragraph, never baked into the image
    c = doc.add_paragraph()
    c.paragraph_format.space_after = Pt(12)
    c.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    add_runs(c, caption, size=10)


# ---------------------------------------------------------------- parsing
def load_manuscript():
    src = os.path.join(ROOT, "manuscript-diffusion-before-adoption.md")
    t = open(src).read()
    title = t.split("\n")[0].lstrip("# ").strip()
    figs_start = t.index("## Figures")
    tab_start = t.index("## Table 1.")
    ref_start = t.index("## References")
    body = t[t.index("## Abstract"):figs_start]
    figs_md = t[figs_start:tab_start]
    table_md = t[tab_start:ref_start]
    refs_md = t[ref_start:]
    return title, body, figs_md, table_md, refs_md


def parse_figures(figs_md):
    """{n: (spec_paragraph, caption_paragraph)} keyed by figure number."""
    out = {}
    blocks = re.split(r"\n(?=\*\*Figure )", figs_md)
    for b in blocks:
        m = re.match(r"\*\*Figure (\d)\.", b.strip())
        if not m:
            continue
        n = int(m.group(1))
        cap = ""
        cm = re.search(r"\*Caption\.\*(.+?)(?:\n\n|\Z)", b, re.S)
        if cm:
            cap = "*Caption.* " + " ".join(cm.group(1).split())
        head = b.strip().split("\n")[0]
        title = re.sub(r"^\*\*|\*\*$", "", head)
        out[n] = (title, cap)
    return out



# --------------------------------------------------------------- overwrite guard
BASELINE = os.path.join(OUTDIR, ".generated-baseline")


def refuse_if_hand_edited(path):
    """Do not clobber a DOCX the authors have edited by hand.

    Once prose editing moves into Word, the DOCX is the source of truth and this
    script must not run against it. The baseline manifest records the md5 of the
    file as generated; if the file on disk no longer matches, someone has edited
    it and regenerating would destroy that work.
    """
    import hashlib, json
    man = os.path.join(BASELINE, "manifest.json")
    if not os.path.exists(man) or not os.path.exists(path):
        return
    rec = json.load(open(man)).get(os.path.basename(path))
    if not rec:
        return
    cur = hashlib.md5(open(path, "rb").read()).hexdigest()
    if cur != rec["md5"]:
        sys.exit(
            f"REFUSING TO OVERWRITE {os.path.basename(path)}\n"
            f"  It has been edited since it was generated on {rec['generated']}.\n"
            f"  The DOCX is now the source of truth. Regenerating would destroy that work.\n"
            f"  A pristine copy of the generated version is in {os.path.relpath(BASELINE, ROOT)}/.\n"
            f"  To rebuild anyway, delete the manifest entry deliberately.")


# ------------------------------------------------------------------ build
def build_main():
    title, body, figs_md, table_md, refs_md = load_manuscript()
    figs = parse_figures(figs_md)
    doc = base_document()
    add_page_numbers(doc)

    h = doc.add_paragraph(); h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    h.paragraph_format.space_after = Pt(18)
    r = h.add_run(title); r.bold = True; r.font.size = Pt(15); r.font.name = BODY_FONT

    table_rows = [l for l in table_md.split("\n") if l.startswith("|")]
    table_caption = table_md.split("\n")[0].lstrip("# ").strip()
    table_note = ""
    nm = re.search(r"\*Note\.\*(.+)", table_md)
    if nm:
        table_note = "*Note.* " + " ".join(nm.group(1).split())

    placed_figs, placed_table = set(), False
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip():
            i += 1; continue
        if ln.startswith("---"):
            i += 1; continue
        if ln.startswith("### "):
            doc.add_paragraph(ln[4:].strip(), style="Heading 3"); i += 1; continue
        if ln.startswith("## "):
            head = ln[3:].strip()
            doc.add_paragraph(head, style="Heading 1")
            i += 1; continue
        if ln.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(4)
            add_runs(p, ln[2:].strip())
            i += 1; continue
        para(doc, ln.strip())
        # place Table 1 right after the paragraph that first cites it
        if not placed_table and "Table 1" in ln:
            cap = doc.add_paragraph(); cap.paragraph_format.space_before = Pt(12)
            cap.paragraph_format.space_after = Pt(4)
            cap.paragraph_format.keep_with_next = True
            add_runs(cap, f"**{table_caption}**", size=10)
            md_table(doc, table_rows)
            if table_note:
                n = doc.add_paragraph(); n.paragraph_format.space_after = Pt(12)
                n.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                add_runs(n, table_note, size=9)
            placed_table = True
        # place each figure after the paragraph that first calls it
        for n in sorted(figs):
            if n in placed_figs:
                continue
            if re.search(rf"Figure {n}\b", ln):
                title_, cap = figs[n]
                add_figure(doc, n, f"**{title_}** {cap.replace('*Caption.* ', '')}")
                placed_figs.add(n)
        i += 1

    for n in sorted(figs):
        if n not in placed_figs:
            title_, cap = figs[n]
            add_figure(doc, n, f"**{title_}** {cap.replace('*Caption.* ', '')}")

    doc.add_paragraph("References", style="Heading 1")
    for ln in refs_md.split("\n")[1:]:
        if not ln.strip():
            continue
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.first_line_indent = Inches(-0.5)
        p.paragraph_format.left_indent = Inches(0.5)
        add_runs(p, ln.strip())

    out = os.path.join(OUTDIR, "Diffusion_Before_Adoption_Main_Manuscript_Blinded.docx")
    refuse_if_hand_edited(out)
    doc.save(out)
    return out, len(placed_figs), placed_table


def build_supplement():
    src = os.path.join(ROOT, "supplement-diffusion-before-adoption.md")
    t = open(src).read()
    doc = base_document()
    add_page_numbers(doc)
    supfigs = {
        "S-a": "figureS_carrier_sensitivity.png",
        "S-b": "figureS_advocates.png",
    }
    lines = t.split("\n")
    i = 0
    while i < len(lines):
        ln = lines[i].rstrip()
        if not ln.strip() or ln.startswith("---"):
            i += 1; continue
        if ln.startswith("### "):
            doc.add_paragraph(ln[4:].strip(), style="Heading 3"); i += 1; continue
        if ln.startswith("## "):
            doc.add_paragraph(ln[3:].strip(), style="Heading 1"); i += 1; continue
        if ln.startswith("# "):
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(ln[2:].strip()); r.bold = True; r.font.size = Pt(15)
            r.font.name = BODY_FONT
            i += 1; continue
        if ln.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i]); i += 1
            md_table(doc, block)
            doc.add_paragraph().paragraph_format.space_after = Pt(8)
            continue
        if ln.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            i += 1
            for c in code:
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                r = p.add_run(c if c.strip() else " ")
                r.font.name = "Consolas"; r.font.size = Pt(9)
            doc.add_paragraph().paragraph_format.space_after = Pt(8)
            continue
        if ln.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(4)
            add_runs(p, ln[2:].strip()); i += 1; continue
        para(doc, ln.strip())
        i += 1

    doc.add_paragraph("Supplementary Figures", style="Heading 1")
    caps = {
        "S-a": ("**Figure S1. Carrier threshold sensitivity.** Carrier fraction over time under a "
                "threshold of at least one relevant component and at least two (which is k minus 1 "
                "here), under scheduled activation (Panel A) and endogenous activation (Panel B). "
                "Dotted horizontals mark the value at initialization; diamonds mark run-end values. "
                "The weak threshold begins at 0.474 from seeding alone, so its endpoint understates "
                "what diffusion contributes. The stricter threshold begins at 0.109 and rises to "
                "0.791 under scheduled activation and 0.562 under endogenous activation."),
        "S-b": ("**Figure S2. Manifest advocates and latent conversion.** Panel A: manifest adoption "
                "and carrier fraction against seeded share, at higher capacity (C=6) and lower "
                "capacity (C=5). Panel B: final adoption against advocate transmission multiplier on "
                "a log base 2 axis, showing the sign change between capacity conditions."),
    }
    for k, fn in supfigs.items():
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(12); p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(os.path.join(FIGDIR, fn), width=Inches(6.3))
        c = doc.add_paragraph(); c.paragraph_format.space_after = Pt(12)
        c.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        add_runs(c, caps[k], size=10)

    out = os.path.join(OUTDIR, "Diffusion_Before_Adoption_Online_Supplement.docx")
    refuse_if_hand_edited(out)
    doc.save(out)
    return out


if __name__ == "__main__":
    m, nfig, tab = build_main()
    print(f"main -> {os.path.relpath(m, ROOT)}  ({nfig} figures inline, Table 1 placed={tab})")
    s = build_supplement()
    print(f"supplement -> {os.path.relpath(s, ROOT)}")
