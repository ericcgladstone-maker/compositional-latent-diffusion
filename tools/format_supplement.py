#!/usr/bin/env python3
"""FORMAT-ONLY typesetting pass for the online supplement.

Changes presentation only. No text node is added, removed, or altered.
Empty formatting-only paragraphs may be dropped (authorized), and section-break
carrier paragraphs may be added (authorized) -- neither carries visible text.

  python3 tools/format_supplement.py
"""
import shutil, sys
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

SRC = "submission/Diffusion_Before_Adoption_Supplement_Metric_Repair.docx"
OUT = "submission/Diffusion_Before_Adoption_Supplement_Formatted.docx"

SERIF = "Times New Roman"
MONO  = "Courier New"
BODY_PT, TABLE_PT, DENSE_PT, CODE_PT = 10.0, 9.0, 8.5, 8.0
CODE_START, CODE_END = 19, 106          # pseudocode paragraph range (inclusive)

# ---------------------------------------------------------------- low level
def _sub(parent, tag):
    el = parent.find(qn(tag))
    if el is None:
        el = OxmlElement(tag); parent.append(el)
    return el

def _pPr(p):  return _sub(p._p, 'w:pPr')
def _rPr(r):  return _sub(r._r, 'w:rPr')

def run_fmt(r, name=None, size=None, bold=None, italic=None, color="000000"):
    rPr = _rPr(r)
    if name:
        f = _sub(rPr, 'w:rFonts')
        for a in ('w:ascii', 'w:hAnsi', 'w:cs'):
            f.set(qn(a), name)
        # clear any theme font that would override
        f.set(qn('w:eastAsia'), name)
        for a in ('w:asciiTheme', 'w:hAnsiTheme', 'w:cstheme', 'w:eastAsiaTheme'):
            if f.get(qn(a)) is not None: del f.attrib[qn(a)]
    if size is not None:
        for tag in ('w:sz', 'w:szCs'):
            _sub(rPr, tag).set(qn('w:val'), str(int(round(size * 2))))
    if bold is not None:
        b = _sub(rPr, 'w:b'); b.set(qn('w:val'), '1' if bold else '0')
    if italic is not None:
        i = _sub(rPr, 'w:i'); i.set(qn('w:val'), '1' if italic else '0')
    if color is not None:
        _sub(rPr, 'w:color').set(qn('w:val'), color)
    # strip highlight / shading / underline artifacts
    for tag in ('w:highlight', 'w:shd', 'w:u'):
        el = rPr.find(qn(tag))
        if el is not None: rPr.remove(el)

def para_fmt(p, before=None, after=None, line=None, align=None,
             keep_next=None, keep_lines=None, widow=True,
             left_indent=None, first_line=None, hanging=None):
    pPr = _pPr(p)
    sp = _sub(pPr, 'w:spacing')
    if before is not None: sp.set(qn('w:before'), str(int(before * 20)))
    if after  is not None: sp.set(qn('w:after'),  str(int(after * 20)))
    if line   is not None:
        sp.set(qn('w:line'), str(int(line * 240))); sp.set(qn('w:lineRule'), 'auto')
    if align is not None: p.alignment = align
    if keep_next is not None:
        k = _sub(pPr, 'w:keepNext'); k.set(qn('w:val'), '1' if keep_next else '0')
    if keep_lines is not None:
        k = _sub(pPr, 'w:keepLines'); k.set(qn('w:val'), '1' if keep_lines else '0')
    if widow is not None:
        w = _sub(pPr, 'w:widowControl'); w.set(qn('w:val'), '1' if widow else '0')
    if left_indent is not None or first_line is not None or hanging is not None:
        ind = _sub(pPr, 'w:ind')
        if left_indent is not None: ind.set(qn('w:left'), str(int(left_indent * 1440)))
        if first_line is not None:  ind.set(qn('w:firstLine'), str(int(first_line * 1440)))
        if hanging is not None:     ind.set(qn('w:hanging'), str(int(hanging * 1440)))

def mark_fmt(p, name, size, bold=None):
    """Format the paragraph mark. Bullets and field results follow this."""
    rPr = _sub(_pPr(p), 'w:rPr')
    f = _sub(rPr, 'w:rFonts')
    for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): f.set(qn(a), name)
    for tag in ('w:sz', 'w:szCs'):
        _sub(rPr, tag).set(qn('w:val'), str(int(round(size * 2))))
    if bold is not None:
        b = _sub(rPr, 'w:b'); b.set(qn('w:val'), '1' if bold else '0')
    _sub(rPr, 'w:color').set(qn('w:val'), '000000')

def cell_margins(tbl, top=0.04, bottom=0.04, left=0.06, right=0.06):
    tblPr = tbl._tbl.tblPr
    mar = _sub(tblPr, 'w:tblCellMar')
    for tag, v in (('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)):
        el = _sub(mar, tag)
        el.set(qn('w:w'), str(int(v * 1440))); el.set(qn('w:type'), 'dxa')

def table_borders(tbl, hair="6", rule="8"):
    """Thin top/header/bottom rules, very light row separators, no vertical grid."""
    tblPr = tbl._tbl.tblPr
    old = tblPr.find(qn('w:tblBorders'))
    if old is not None: tblPr.remove(old)
    b = OxmlElement('w:tblBorders')
    spec = {'top': ('single', rule, '000000'), 'bottom': ('single', rule, '000000'),
            'left': ('none', '0', 'auto'),     'right': ('none', '0', 'auto'),
            'insideH': ('single', hair, 'BFBFBF'), 'insideV': ('none', '0', 'auto')}
    for k, (val, sz, col) in spec.items():
        e = OxmlElement('w:' + k)
        e.set(qn('w:val'), val); e.set(qn('w:sz'), sz)
        e.set(qn('w:space'), '0'); e.set(qn('w:color'), col)
        b.append(e)
    tblPr.append(b)

def shade(cell, fill="F2F2F2"):
    tcPr = cell._tc.get_or_add_tcPr()
    s = _sub(tcPr, 'w:shd')
    s.set(qn('w:val'), 'clear'); s.set(qn('w:color'), 'auto'); s.set(qn('w:fill'), fill)

def repeat_header(row):
    trPr = _sub(row._tr, 'w:trPr')
    _sub(trPr, 'w:tblHeader').set(qn('w:val'), '1')

def cant_split(row):
    trPr = _sub(row._tr, 'w:trPr')
    _sub(trPr, 'w:cantSplit').set(qn('w:val'), '1')

def fixed_layout(tbl, total_in):
    tblPr = tbl._tbl.tblPr
    lay = _sub(tblPr, 'w:tblLayout'); lay.set(qn('w:type'), 'fixed')
    w = _sub(tblPr, 'w:tblW')
    w.set(qn('w:w'), str(int(total_in * 1440))); w.set(qn('w:type'), 'dxa')

def col_widths(tbl, fracs, total_in):
    fixed_layout(tbl, total_in)
    widths = [Inches(total_in * f) for f in fracs]
    grid = tbl._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for gc, w in zip(grid.findall(qn('w:gridCol')), widths):
            gc.set(qn('w:w'), str(int(w.emu / 635)))   # EMU -> twips
    for row in tbl.rows:
        for cell, w in zip(row.cells, widths):
            cell.width = w

def vert_top(tbl):
    for row in tbl.rows:
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.TOP

# ---------------------------------------------------------------- main pass
def main():
    shutil.copy2(SRC, OUT)
    doc = Document(OUT)
    log = []

    # -- IV. page setup -----------------------------------------------------
    for s in doc.sections:
        s.orientation = WD_ORIENT.PORTRAIT
        s.page_width, s.page_height = Inches(8.5), Inches(11)
        for a in ('top_margin', 'bottom_margin', 'left_margin', 'right_margin'):
            setattr(s, a, Inches(0.75))
    PORT_W = 8.5 - 1.5      # 7.00 in usable
    LAND_W = 11.0 - 1.2     # 9.80 in usable
    log.append("page: Letter portrait, 0.75in margins, usable 7.00in "
               "(landscape 9.80in at 0.60in margins)")

    paras = doc.paragraphs
    code_els = {id(paras[i]._p) for i in range(CODE_START, CODE_END + 1)}

    # -- XX. drop empty formatting-only paragraphs (never inside code block) --
    dropped = 0
    for p in list(paras):
        if p.text.strip() or id(p._p) in code_els:
            continue
        x = p._p.xml
        if any(t in x for t in ('<w:drawing', '<w:sectPr', 'bookmarkStart',
                                'commentRange', 'commentReference', '<w:hyperlink',
                                '<w:fldChar', '<w:instrText', '<w:pict', '<w:object')):
            continue
        p._p.getparent().remove(p._p)
        dropped += 1
    log.append(f"removed {dropped} empty formatting-only paragraphs "
               f"(pseudocode blank lines preserved)")

    # -- V/VI. paragraph typography ----------------------------------------
    H1 = "Heading 1"
    counts = {"title": 0, "h1": 0, "sub": 0, "body": 0, "code": 0}
    for i, p in enumerate(doc.paragraphs):
        st = p.style.name
        is_code = id(p._p) in code_els

        if is_code:                                   # VIII. pseudocode
            para_fmt(p, before=0, after=0, line=1.0, align=WD_ALIGN_PARAGRAPH.LEFT,
                     keep_next=False, keep_lines=False, widow=False,
                     left_indent=0.18, first_line=0)
            for r in p.runs:
                run_fmt(r, MONO, CODE_PT, bold=False, italic=False, color="000000")
            # The paragraph MARK carries its own font. Empty code lines have no
            # runs, so without this they keep the old 11pt mark and render as
            # ~14pt gaps. Set the mark to the code font, and give blank lines a
            # small exact height so stanzas stay separated without wasting a page.
            mark = _sub(_pPr(p), 'w:rPr')
            mf = _sub(mark, 'w:rFonts')
            for a in ('w:ascii', 'w:hAnsi', 'w:cs'): mf.set(qn(a), MONO)
            for tag in ('w:sz', 'w:szCs'):
                _sub(mark, tag).set(qn('w:val'), str(int(CODE_PT * 2)))
            if not p.text.strip():
                sp = _sub(_pPr(p), 'w:spacing')
                sp.set(qn('w:line'), '110'); sp.set(qn('w:lineRule'), 'exact')
            counts["code"] += 1
            continue

        if i == 0:                                    # VI. supplement title
            para_fmt(p, before=0, after=6, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER,
                     keep_next=True, left_indent=0, first_line=0)
            for r in p.runs: run_fmt(r, SERIF, 14.0, bold=True, color="000000")
            mark_fmt(p, SERIF, 14.0, bold=True)
            counts["title"] += 1; continue
        if i == 1:                                    # article title beneath
            para_fmt(p, before=0, after=6, line=1.0, align=WD_ALIGN_PARAGRAPH.CENTER,
                     keep_next=True, left_indent=0, first_line=0)
            for r in p.runs: run_fmt(r, SERIF, 11.0, bold=False, color="000000")
            mark_fmt(p, SERIF, 11.0, bold=False)
            counts["title"] += 1; continue

        if st == H1:                                  # top-level sections
            para_fmt(p, before=8, after=3, line=1.0, align=WD_ALIGN_PARAGRAPH.LEFT,
                     keep_next=True, keep_lines=True, left_indent=0, first_line=0)
            for r in p.runs:
                run_fmt(r, SERIF, 12.0, bold=True, italic=False, color="000000")
            mark_fmt(p, SERIF, 12.0, bold=True)
            counts["h1"] += 1
        elif st.startswith("Heading"):                # subsections
            para_fmt(p, before=6, after=2, line=1.0, align=WD_ALIGN_PARAGRAPH.LEFT,
                     keep_next=True, keep_lines=True, left_indent=0, first_line=0)
            for r in p.runs:
                run_fmt(r, SERIF, 10.5, bold=True, italic=False, color="000000")
            mark_fmt(p, SERIF, 10.5, bold=True)
            counts["sub"] += 1
        else:                                         # body
            para_fmt(p, before=0, after=3, line=1.03, align=WD_ALIGN_PARAGRAPH.LEFT,
                     keep_next=False, widow=True)
            for r in p.runs:
                # VII. inline identifiers: serif, black, body size -- no code pills
                run_fmt(r, SERIF, BODY_PT, color="000000")
            mark_fmt(p, SERIF, BODY_PT)      # keeps list bullets at body size
            counts["body"] += 1
    # VIII. Keep each pseudocode stanza together so a page break can only fall
    # on a blank line -- i.e. between logical stages, never mid-clause.
    code_ps = [p for p in doc.paragraphs if id(p._p) in code_els]
    chained = 0
    for i, p in enumerate(code_ps[:-1]):
        nxt = code_ps[i + 1]
        keep = bool(p.text.strip()) and bool(nxt.text.strip())
        k = _sub(_pPr(p), 'w:keepNext'); k.set(qn('w:val'), '1' if keep else '0')
        chained += keep
    log.append(f"pseudocode: {len(code_ps)} lines at {CODE_PT}pt {MONO}; "
               f"{chained} keepNext links so breaks fall only between stanzas")

    log.append("typography: body {}pt, H1 {}pt bold, sub {}pt bold, code {}pt {} "
               "({} body / {} h1 / {} sub / {} code paras)".format(
                   BODY_PT, 12.0, 10.5, CODE_PT, MONO,
                   counts["body"], counts["h1"], counts["sub"], counts["code"]))
    return doc, log, PORT_W, LAND_W

# ---------------------------------------------------------------- tables etc
NUMERIC = ("0","1","2","3","4","5","6","7","8","9","−","-","+",".")

def looks_numeric(s):
    s = s.strip()
    if not s: return False
    return all(c in "0123456789.,+-−±()% " for c in s) and any(c.isdigit() for c in s)

def format_tables(doc, PORT_W, LAND_W, wide_ids, log):
    from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
    # per-spec column fraction plans, keyed by table index (1-based)
    PLAN = {
        10: dict(w=LAND_W, pt=DENSE_PT, hpt=8.0,
                 fr=[.055,.065,.135,.115,.115,.115,.10,.115,.185]),   # S5.3 (9 col)
        25: dict(w=LAND_W, pt=8.0, hpt=8.0,
                 fr=[.175,.105,.055,.13,.155,.38]),                   # Table S1
        26: dict(w=LAND_W, pt=8.0, hpt=8.0,
                 fr=[.175,.085,.055,.135,.165,.385]),                 # Table S2
        # Table S3 at 8.0pt (Section XV allows 8-8.25) so the final two rows do
        # not spill onto a near-empty landscape page.
        27: dict(w=LAND_W, pt=8.0, hpt=8.0,
                 fr=[.14,.16,.18,.21,.13,.18]),                       # Table S3
        28: dict(w=PORT_W, pt=8.5, hpt=8.5, fr=[.36,.14,.50]),        # impl audit
    }
    n_reformatted = 0
    for ti, tbl in enumerate(doc.tables, start=1):
        plan = PLAN.get(ti)
        width = plan["w"] if plan else PORT_W
        body_pt = plan["pt"] if plan else TABLE_PT
        hdr_pt  = plan["hpt"] if plan else 8.5

        table_borders(tbl)
        cell_margins(tbl)
        vert_top(tbl)
        if plan:
            col_widths(tbl, plan["fr"], width)
        else:
            fixed_layout(tbl, width)
            n = len(tbl.columns)
            col_widths(tbl, [1.0 / n] * n, width)

        # X. Alignment is decided per COLUMN, not per cell, so a mixed-type
        # column (e.g. Default = 8 / 0.1 / set_sufficiency) stays visually flush
        # instead of alternating left and right cell by cell.
        ncol = len(tbl.columns)
        col_align = []
        for ci in range(ncol):
            col = [tbl.rows[k].cells[ci].text for k in range(1, len(tbl.rows))]
            col_align.append(AL.RIGHT if col and
                             sum(map(looks_numeric, col)) > len(col) / 2 else AL.LEFT)

        for ri, row in enumerate(tbl.rows):
            # The Google-Docs export baked portrait row heights into every row
            # (atLeast, up to 2450 twips). Strip them so rows size to content.
            trPr = row._tr.find(qn('w:trPr'))
            if trPr is not None:
                h = trPr.find(qn('w:trHeight'))
                if h is not None: trPr.remove(h)
            cant_split(row)
            if ri == 0:
                repeat_header(row)
            for ci, cell in enumerate(row.cells):
                if ri == 0:
                    shade(cell, "F2F2F2")
                for p in cell.paragraphs:
                    txt = p.text
                    al = col_align[ci] if ci < len(col_align) else AL.LEFT
                    para_fmt(p, before=0, after=0, line=1.0, align=al,
                             keep_next=False, widow=False, left_indent=0, first_line=0)
                    for r in p.runs:
                        run_fmt(r, SERIF,
                                hdr_pt if ri == 0 else body_pt,
                                bold=True if ri == 0 else None,
                                color="000000")
        n_reformatted += 1
    log.append(f"tables: {n_reformatted} reformatted; header rows bold + 10% gray, "
               f"repeat-on-page enabled, rows kept together, top-aligned, "
               f"numeric columns right-aligned")
    return n_reformatted

def format_refs_and_captions(doc, log):
    """XVIII references 9.5pt hanging; XIX captions 9pt."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
    ps = doc.paragraphs
    ref_start = None
    for i, p in enumerate(ps):
        if p.style.name == "Heading 1" and p.text.strip() == "References":
            ref_start = i; break
    nref = ncap = 0
    for i, p in enumerate(ps):
        t = p.text.strip()
        if t.startswith("Figure S"):
            para_fmt(p, before=2, after=4, line=1.0, align=AL.LEFT,
                     keep_next=False, left_indent=0, first_line=0)
            for r in p.runs: run_fmt(r, SERIF, 9.0, color="000000")
            ncap += 1
        elif (ref_start is not None and i > ref_start and t
              and not p.style.name.startswith("Heading")):
            para_fmt(p, before=0, after=2, line=1.0, align=AL.LEFT,
                     left_indent=0.25, hanging=0.25)
            for r in p.runs: run_fmt(r, SERIF, 9.5, color="000000")
            nref += 1
    log.append(f"references: {nref} entries at 9.5pt with 0.25in hanging indent; "
               f"{ncap} figure captions at 9pt")

def size_figures(doc, PORT_W, log):
    """XIX resize proportionally, centre; never touch image bytes."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
    MAXW = min(6.9, PORT_W)
    out = []
    for sh in doc.inline_shapes:
        ar = sh.width.inches / sh.height.inches
        if sh.width.inches > MAXW:
            sh.width = Inches(MAXW); sh.height = Inches(MAXW / ar)
        out.append((round(sh.width.inches, 3), round(sh.height.inches, 3), round(ar, 4)))
    for p in doc.paragraphs:
        if '<w:drawing' in p._p.xml:
            para_fmt(p, before=2, after=2, line=1.0, align=AL.CENTER,
                     keep_next=True, left_indent=0, first_line=0)
    # XIX/XXI. Chain keepNext from the "Supplementary Figures" heading through
    # the last caption so a figure is never separated from its caption and the
    # two figures travel together onto one page.
    ps = doc.paragraphs
    start = None
    for i, p in enumerate(ps):
        if p.text.strip() == "Supplementary Figures":
            start = i; break
    linked = 0
    if start is not None:
        block = [p for p in ps[start:] if p.text.strip() or '<w:drawing' in p._p.xml]
        for p in block[:-1]:
            k = _sub(_pPr(p), 'w:keepNext'); k.set(qn('w:val'), '1'); linked += 1
        last = _sub(_pPr(block[-1]), 'w:keepNext'); last.set(qn('w:val'), '0')
    log.append(f"figures: {len(out)} centred, resized proportionally to <= {MAXW}in "
               f"-> {out}; {linked} keepNext links hold the figure block together")

# ---------------------------------------------------------- section breaks
def _sectPr(landscape):
    """Build a nextPage sectPr. Never odd/even (XXIX)."""
    sp = OxmlElement('w:sectPr')
    t = OxmlElement('w:type'); t.set(qn('w:val'), 'nextPage'); sp.append(t)
    sz = OxmlElement('w:pgSz')
    if landscape:
        sz.set(qn('w:w'), str(int(11.0 * 1440))); sz.set(qn('w:h'), str(int(8.5 * 1440)))
        sz.set(qn('w:orient'), 'landscape'); m = 0.60
    else:
        sz.set(qn('w:w'), str(int(8.5 * 1440))); sz.set(qn('w:h'), str(int(11.0 * 1440)))
        sz.set(qn('w:orient'), 'portrait');  m = 0.75
    sp.append(sz)
    mar = OxmlElement('w:pgMar')
    for a, v in (('w:top', m), ('w:bottom', m), ('w:left', m), ('w:right', m)):
        mar.set(qn(a), str(int(v * 1440)))
    mar.set(qn('w:header'), '432'); mar.set(qn('w:footer'), '432'); mar.set(qn('w:gutter'), '0')
    sp.append(mar)
    return sp

def _carrier(landscape):
    """Empty paragraph carrying a sectPr. Holds no visible text."""
    p = OxmlElement('w:p')
    pPr = OxmlElement('w:pPr')
    sp = OxmlElement('w:spacing')
    for a in ('w:before', 'w:after'): sp.set(qn(a), '0')
    sp.set(qn('w:line'), '20'); sp.set(qn('w:lineRule'), 'exact')
    pPr.append(sp)
    rPr = OxmlElement('w:rPr')
    szv = OxmlElement('w:sz'); szv.set(qn('w:val'), '2'); rPr.append(szv)
    pPr.append(rPr)
    pPr.append(_sectPr(landscape))
    p.append(pPr)
    return p

def make_landscape(doc, groups, log):
    """groups: list of (first_element, last_element) to place in landscape."""
    body = doc.element.body
    for first, last in groups:
        body.insert(list(body).index(first), _carrier(landscape=False))   # end portrait
        body.insert(list(body).index(last) + 1, _carrier(landscape=True)) # end landscape
    # The source carried <w:pgNumType w:start="1"/> on the single body sectPr.
    # Harmless in a one-section file, but it now governs the LAST section and
    # would restart page numbering there. Strip it so numbering is continuous.
    body_sect = body.find(qn('w:sectPr'))
    if body_sect is not None:
        pn = body_sect.find(qn('w:pgNumType'))
        if pn is not None:
            body_sect.remove(pn)
            log.append("removed pgNumType restart from final section "
                       "(numbering now continuous across all 5 sections)")
    log.append(f"landscape: {len(groups)} sections created (nextPage breaks, "
               f"0.60in margins, continuous numbering)")

def fix_style_defaults(doc, log):
    """The Google-Docs export left docDefaults at Cambria 12pt. Everything
    inherits it, including the Footer style -- which is why a regenerated PAGE
    field renders 12pt Cambria no matter how the run is formatted. Set sane
    defaults and pin the Footer style explicitly."""
    st = doc.styles.element
    dd = st.find(qn('w:docDefaults'))
    if dd is not None:
        rd = dd.find(qn('w:rPrDefault'))
        if rd is not None:
            rPr = _sub(rd, 'w:rPr')
            f = _sub(rPr, 'w:rFonts')
            for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): f.set(qn(a), SERIF)
            for tag in ('w:sz', 'w:szCs'):
                _sub(rPr, tag).set(qn('w:val'), str(int(BODY_PT * 2)))
    for sid, pt in (('Footer', 9.0), ('Header', 9.0)):
        el = None
        for style in st.findall(qn('w:style')):
            if style.get(qn('w:styleId')) == sid: el = style; break
        if el is None: continue
        rPr = _sub(el, 'w:rPr')
        f = _sub(rPr, 'w:rFonts')
        for a in ('w:ascii', 'w:hAnsi', 'w:cs', 'w:eastAsia'): f.set(qn(a), SERIF)
        for tag in ('w:sz', 'w:szCs'):
            _sub(rPr, tag).set(qn('w:val'), str(int(pt * 2)))
    log.append(f"styles: docDefaults set to {SERIF} {BODY_PT}pt "
               f"(was Cambria 12pt); Footer/Header pinned to 9pt")

def add_footer_page_numbers(doc, log):
    """XXV. centred 9pt page number in the footer of every section."""
    from docx.enum.text import WD_ALIGN_PARAGRAPH as AL
    for si, s in enumerate(doc.sections):
        s.different_first_page_header_footer = False
        f = s.footer
        if si > 0:
            f.is_linked_to_previous = True
            continue
        f.is_linked_to_previous = False
        p = f.paragraphs[0] if f.paragraphs else f.add_paragraph()
        for r in list(p.runs): r._r.getparent().remove(r._r)
        p.alignment = AL.CENTER
        para_fmt(p, before=0, after=0, line=1.0, align=AL.CENTER,
                 left_indent=0, first_line=0)
        mark_fmt(p, SERIF, 9.0, bold=False)
        # A PAGE field needs a *result* run to carry the visible formatting.
        # begin/instrText/end alone leaves nothing to format, and the renderer
        # falls back to the Footer style (Cambria 12pt). fldSimple wraps a real,
        # formatted result run, which both Word and LibreOffice honour.
        fld = OxmlElement('w:fldSimple')
        fld.set(qn('w:instr'), ' PAGE ')
        inner = OxmlElement('w:r')
        p._p.append(fld); fld.append(inner)
        from docx.text.run import Run
        r = Run(inner, p)
        r.text = '1'                      # cached result; Word recomputes on open
        run_fmt(r, SERIF, 9.0, bold=False, color="000000")
    log.append("footer: centred PAGE field, 9pt, linked across all sections")

# ------------------------------------------------------------------ driver
if __name__ == "__main__":
    doc, log, PORT_W, LAND_W = main()

    from docx.table import Table
    from docx.text.paragraph import Paragraph
    body = doc.element.body
    kids = list(body)

    def para_el(pred):
        for ch in kids:
            if ch.tag.endswith('}p'):
                if pred(Paragraph(ch, doc)): return ch
        return None

    tbl_els = [ch for ch in kids if ch.tag.endswith('}tbl')]
    g1_first = para_el(lambda p: p.text.strip() == "S5.3 Results")
    g1_last  = tbl_els[9]                      # T10, S5.3 results
    g2_first = para_el(lambda p: p.text.strip().startswith("Table S1."))
    g2_last  = tbl_els[26]                     # T27, Table S3
    assert None not in (g1_first, g2_first), "landscape anchors not found"

    format_tables(doc, PORT_W, LAND_W, {10, 25, 26, 27}, log)
    format_refs_and_captions(doc, log)
    size_figures(doc, PORT_W, log)
    make_landscape(doc, [(g1_first, g1_last), (g2_first, g2_last)], log)
    fix_style_defaults(doc, log)
    add_footer_page_numbers(doc, log)

    doc.save(OUT)

    # XXXIV. OOXML measurement attributes are integers. The Google-Docs export
    # already carried 79 float values, and python-docx's width setter adds more.
    # Word tolerates them; a strict validator does not. Round them in place --
    # sub-twip precision has no layout consequence (1 twip = 1/1440 inch).
    import re as _re, zipfile as _zip, shutil as _sh, os as _os
    fixed = [0]
    tmp = OUT + ".tmp"
    zin = _zip.ZipFile(OUT); zout = _zip.ZipFile(tmp, "w", _zip.ZIP_DEFLATED)
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.endswith(".xml"):
            txt = data.decode("utf8")
            def _round(m):
                fixed[0] += 1
                return '%s="%d"' % (m.group(1), round(float(m.group(2))))
            txt2 = _re.sub(r'(w:w|w:h|w:left|w:right|w:top|w:bottom|w:firstLine|w:hanging)'
                           r'="(-?\d+\.\d+)"', _round, txt)
            data = txt2.encode("utf8")
        zout.writestr(item, data)
    zin.close(); zout.close(); _os.replace(tmp, OUT)
    log.append(f"xml: rounded {fixed[0]} float measurement attributes to integers")

    print("wrote", OUT)
    for line in log: print("  -", line)
