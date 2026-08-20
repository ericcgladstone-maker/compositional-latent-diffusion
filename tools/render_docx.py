#!/usr/bin/env python3
"""Render a .docx to paged PNGs so a page-level visual QC is possible.

There is no Word or LibreOffice on this machine. This pipeline uses what is:

    docx --(mammoth)--> HTML --(headless Chrome)--> PDF --(PyMuPDF)--> PNG/page

IMPORTANT: this is a PROXY renderer, not Word's layout engine. Page size,
margins, fonts and sizes are matched to the document's own section properties,
so it is reliable for catching oversized figures, over-wide tables, orphaned
captions, style inconsistency and gross spacing problems. It is NOT
authoritative for exactly where Word will break a page.

    python3 tools/render_docx.py <file.docx> [outdir] [--dpi N] [--pages A-B]
"""
import os, subprocess, sys, base64, re

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

CSS = """
@page { size: %(pw).2fin %(ph).2fin; margin: %(mt).2fin %(mr).2fin %(mb).2fin %(ml).2fin; }
html, body { margin:0; padding:0; }
body { font-family: "Times New Roman", Times, serif; font-size: 11pt; line-height: 1.5;
       color:#000; -webkit-print-color-adjust: exact; }
p { margin: 0 0 .55em 0; text-align: left; }
h1 { font-size: 14pt; margin: 1.1em 0 .45em; page-break-after: avoid; }
h2 { font-size: 12.5pt; margin: 1.0em 0 .40em; page-break-after: avoid; }
h3 { font-size: 11.5pt; margin: .95em 0 .35em; page-break-after: avoid; }
h4 { font-size: 11pt; font-style: italic; margin: .85em 0 .3em; page-break-after: avoid; }
img { max-width: 100%%; height: auto; }
table { border-collapse: collapse; width: 100%%; font-size: 9pt; margin: .5em 0 .9em;
        page-break-inside: avoid; }
th, td { border: .5pt solid #999; padding: 3pt 4pt; vertical-align: top; text-align: left; }
tr { page-break-inside: avoid; }
/* pseudocode blocks arrive as normal paragraphs with leading spaces */
p.code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 8.5pt;
         white-space: pre; margin: 0; line-height: 1.25; }
.pagemark { display:none; }
"""

def main():
    src = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "render"
    dpi = 110
    for i, a in enumerate(sys.argv):
        if a == "--dpi": dpi = int(sys.argv[i+1])
    os.makedirs(outdir, exist_ok=True)

    from docx import Document
    import mammoth, fitz

    d = Document(src)
    s = d.sections[0]
    geom = dict(pw=s.page_width.inches, ph=s.page_height.inches,
                mt=s.top_margin.inches, mr=s.right_margin.inches,
                mb=s.bottom_margin.inches, ml=s.left_margin.inches)

    with open(src, "rb") as f:
        res = mammoth.convert_to_html(f)
    html = res.value

    # mark monospace-looking paragraphs (pseudocode uses leading spaces / arrows)
    def mark(m):
        inner = m.group(1)
        plain = re.sub(r"<[^>]+>", "", inner)
        if plain.startswith(" ") or "&lt;-" in inner or plain.strip().startswith("#"):
            return '<p class="code">%s</p>' % inner
        return m.group(0)
    html = re.sub(r"<p>(.*?)</p>", mark, html, flags=re.S)

    doc = "<!doctype html><meta charset='utf-8'><style>%s</style><body>%s</body>" % (
        CSS % geom, html)
    hp = os.path.abspath(os.path.join(outdir, "_render.html"))
    open(hp, "w").write(doc)

    pdf = os.path.abspath(os.path.join(outdir, "_render.pdf"))
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--print-to-pdf=" + pdf, "--virtual-time-budget=20000",
                    "file://" + hp],
                   check=True, capture_output=True, timeout=180)

    pdoc = fitz.open(pdf)
    n = pdoc.page_count
    for i in range(n):
        pg = pdoc.load_page(i)
        pix = pg.get_pixmap(dpi=dpi)
        pix.save(os.path.join(outdir, "page-%02d.png" % (i + 1)))
    print("rendered %d pages -> %s/page-NN.png  (dpi=%d)" % (n, outdir, dpi))
    if res.messages:
        print("converter notes:", len(res.messages))
        for m in res.messages[:6]:
            print("  ", m)

main()
