#!/usr/bin/env python3
"""Build the design-documentation memo as a formatted .docx.

Times New Roman 12 throughout, plain bold section titles, no color, no em dashes
or semicolons. Structure: overview, how the model works, parameters, stages,
worked example, open questions, plan. Writes into the Google-Drive-synced folder
beside the other design docs.
"""

import os

from docx import Document
from docx.shared import Pt, Inches, RGBColor


HERE = os.path.dirname(os.path.abspath(__file__))
DRIVE_FOLDER = os.path.dirname(HERE)
OUT = os.path.join(DRIVE_FOLDER, "latent-adoption-build-review.docx")
SERIF = "Times New Roman"


def style_document(doc):
    def restyle(name, size, bold=False, italic=False):
        st = doc.styles[name]
        st.font.name = SERIF
        st.font.size = Pt(size)
        st.font.bold = bold
        st.font.italic = italic
        st.font.color.rgb = RGBColor(0, 0, 0)
    restyle("Normal", 12)
    restyle("Title", 12, bold=True)
    restyle("Heading 1", 12, bold=True)
    restyle("Heading 2", 12, bold=True)
    restyle("List Bullet", 12)
    restyle("List Number", 12)


def set_cell(cell, text, bold=False, size=11):
    cell.text = ""
    p = cell.paragraphs[0]
    r = p.add_run(text)
    r.font.name = SERIF
    r.font.size = Pt(size)
    r.bold = bold


def add_table(doc, header, rows, widths=None, size=11):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    for i, h in enumerate(header):
        set_cell(t.rows[0].cells[i], h, bold=True, size=size)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            set_cell(cells[i], str(val), size=size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    return t


def bullet(doc, head, body):
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(head + " ").bold = True
    p.add_run(body)


def build():
    doc = Document()
    style_document(doc)

    doc.add_heading("Latent Adoption Model: Build Documentation", level=0)
    p = doc.add_paragraph()
    r = p.add_run("Documentation of the model design, its parameters, the staged build, "
                  "and a worked example of a single run, for review.")
    r.italic = True

    # ---- parameters ------------------------------------------------------
    doc.add_heading("Parameters", level=1)
    from abm import config as C
    for grp in C.GROUP_ORDER:
        params = [pp for pp in C.PARAM_SPECS if pp.group == grp]
        if not params:
            continue
        doc.add_heading(C.GROUP_LABELS.get(grp, grp), level=2)
        rows = []
        for pp in params:
            if pp.kind == "choice":
                rng = " / ".join(str(c) for c in pp.choices)
            elif pp.kind == "bool":
                rng = "on / off"
            else:
                rng = f"{pp.low} to {pp.high}"
            rows.append([pp.name, pp.doc, rng, str(pp.default)])
        add_table(doc, ["Parameter", "Meaning", "Range / options", "Default"], rows,
                  widths=[1.4, 2.9, 1.4, 0.7], size=11)

    # ---- stages ----------------------------------------------------------
    doc.add_heading("Stages of the build", level=1)
    doc.add_paragraph(
        "The build is progressive rather than fully crossed. Each stage adds one thing to "
        "the stage before it and serves as its control, and within a stage a single "
        "factor is varied across its range while the rest are held fixed. A full "
        "factorial over every factor is neither tractable nor interpretable. The "
        "progression is what makes each addition's effect attributable, and each later "
        "stage simply turns on one more setting from the parameters above.")
    add_table(doc,
        ["Stage", "What it adds over the prior stage", "What we vary", "What it gets us"],
        [
            ["Free spread",
             "Nothing limits anyone.",
             "Starting amount of pieces",
             "A sanity baseline, so that any later structure can be attributed to the "
             "limits rather than to the machinery."],
            ["Limited attention",
             "A cap on how much each agent can hold, and a minimum combination needed to "
             "be ready.",
             "The cap",
             "The first uneven landscape: pockets of adoption, near-misses one piece "
             "short, and groups that stay out of reach. This is the core result."],
            ["Whole versus piecemeal",
             "A switch for whether a big thing can move whole or only as its separate "
             "pieces.",
             "That switch",
             "The contrast against ordinary contagion, shown in isolation before anything "
             "else is added."],
            ["Add-ons, one at a time",
             "One optional mechanism switched on alone (compression, lock-in, visibility, "
             "bundling, tie strength, slot cost).",
             "That mechanism's strength",
             "The separate, attributable effect of each mechanism."],
            ["Evangelists into an unready population",
             "A small, fully-equipped minority placed where the pieces are otherwise "
             "scarce.",
             "How many evangelists",
             "The failed-diffusion case: a determined push that still cannot move "
             "adoption until the pieces themselves spread."],
        ],
        widths=[1.4, 2.2, 1.0, 1.9])

    # ---- worked example --------------------------------------------------
    doc.add_heading("A worked example: one run of the limited-attention stage", level=1)
    from abm import phases as P
    from abm.model import World
    w = World(P.config_for_phase("V1", {"seed": 0}))
    w.run()
    T = w.n_element_types

    def snap(t):
        h = w.history[t] if 0 <= t < len(w.history) else w.history[-1]
        a, b = h["per_big"]["alpha"], h["per_big"]["beta"]
        return {"t": h["t"], "mean": h["element_saturation"] * T,
                "ready": a["latent"], "short": a["at_risk"],
                "a": a["manifest"], "b": b["manifest"], "gap": h["observability_gap"]}

    last = len(w.history) - 1
    s0, s50, s99, s100, s200, s300, sf = (snap(t) for t in (0, 50, 99, 100, 200, 300, last))
    pct100 = round((s100["a"] + s100["b"]) / (2 * w.n) * 100)

    doc.add_paragraph(
        "To make the mechanics concrete, the following traces a single run of the "
        "limited-attention stage: 100 agents on a small-world network, a capacity of 6, a "
        "four-element requirement with any three sufficient, only pieces transmitted "
        "(never whole big things), two big things (alpha and beta) that share one "
        "element, and a cue every 100 steps, with seed 0. The numbers are from that exact "
        "run, so any step that looks wrong is worth flagging.")

    add_table(doc,
        ["Step", "Mean elements held", "Ready for alpha", "Alpha adopters",
         "Beta adopters", "Observability gap"],
        [[str(s["t"]), f"{s['mean']:.1f}", str(s["ready"]), str(s["a"]), str(s["b"]),
          f"{s['gap']:+.2f}"] for s in (s0, s50, s99, s100, s200, s300, sf)],
        widths=[0.6, 1.4, 1.1, 1.1, 1.1, 1.2])

    bullet(doc, "Seeding (step 0).",
           f"Each agent independently starts holding each of the {T} element types with "
           f"probability 0.15, about one element apiece ({s0['mean']:.1f} on average). "
           f"Only {s0['ready']} agent already holds a sufficient alpha combination and "
           f"{s0['short']} are a single element short. Nothing has manifested.")
    bullet(doc, "Spreading (steps 1 to 100).",
           f"On each step an agent offers one held element to a random neighbor, which "
           f"lands with probability 0.10. Holdings rise steadily, to about "
           f"{s50['mean']:.1f} elements each by step 50 and {s99['mean']:.1f} by step 99.")
    bullet(doc, "Capacity and competition.",
           "Holdings press against the cap of 6. When an agent is full, the least-useful "
           "element makes way, which is where alpha and beta start to compete, because "
           "they share one element and a slot spent on one is unavailable to the other.")
    bullet(doc, "Readiness and the latent reservoir (step 99).",
           f"Just before the first cue, {s99['ready']} agents hold a sufficient alpha "
           f"combination and {s99['short']} are one element short, yet none have adopted. "
           f"The population is primed but inert, and the observability gap is at its "
           f"widest ({s99['gap']:+.2f}), with the elements widespread and the big thing "
           f"nowhere.")
    bullet(doc, "The cue and the first flip (step 100).",
           f"The cue converts every ready agent at once. Alpha goes from 0 to "
           f"{s100['a']} and beta from 0 to {s100['b']}, so adoption jumps from zero to "
           f"about {pct100} percent in a single step. The observability gap collapses from "
           f"{s99['gap']:+.2f} to {s100['gap']:+.2f}. This is the first sudden flip.")
    bullet(doc, "The staircase (steps 200 to 400).",
           f"Spreading continues between cues and more agents cross the threshold, so "
           f"each later cue produces another jump (alpha adopters {s100['a']}, then "
           f"{s200['a']}, {s300['a']}, {sf['a']}). Adopters remain adopters even when "
           f"later churn drops them below the threshold, which is why by the end adoption "
           f"exceeds raw element saturation and the observability gap has turned negative "
           f"({sf['gap']:+.2f}).")
    bullet(doc, "End state.",
           f"By step {sf['t']} there are {sf['a']} alpha adopters and {sf['b']} beta "
           f"adopters, {sf['short']} agent still one element short, and none structurally "
           f"resistant. The run stops when nothing more is moving.")

    # ---- open questions --------------------------------------------------
    doc.add_heading("Open questions and things to consider", level=1)
    bullet(doc, "An interactive version.",
           "The same design can run as an interactive page with live visualizations: the "
           "network coloring by status as it evolves, the adoption and saturation traces "
           "updating in real time, and a slider for every parameter. It is well suited to "
           "hunting for the small-change, large-effect cases described above, where you "
           "nudge a single knob and watch the regime flip. Worth standing up and sharing, "
           "or do we keep to batch runs for now?")
    bullet(doc, "Reversible adoption.",
           "In the worked example an agent that adopts stays an adopter even if it later "
           "loses a constituent element. Whether adoption should instead be reversible, "
           "dropping back when the combination is lost, is a design decision worth "
           "settling.")
    bullet(doc, "Content-specific coupling.",
           "If we want genuine ideological bundles rather than generic crowding, the next "
           "step is letting one big thing raise or lower specific others by name (a "
           "coupling matrix) rather than by one symmetric dial. Worth building now, or "
           "later?")
    bullet(doc, "Which add-ons to carry forward.",
           "Before broadening the runs, which optional mechanisms are worth keeping, and "
           "which should be set aside or examined only under tighter regimes?")
    bullet(doc, "Additional outcome measures.",
           "Curve shape may matter more than the endpoint, so a cascade-shape or timing "
           "statistic would help, a clustering measure would quantify adoption pockets, "
           "and a bundle-correlation measure would be needed once coupling is "
           "content-specific. Which of these are worth adding?")
    bullet(doc, "Making diffusion failure visible.",
           "The evangelist stage needs a comparison without evangelists and a harder "
           "regime, so that failed diffusion shows up as a low curve rather than as mere "
           "insensitivity to the number of evangelists.")

    # ---- plan ------------------------------------------------------------
    doc.add_heading("Plan", level=1)
    doc.add_paragraph(
        "The immediate plan is to run the full staged build described above from end to "
        "end, fully exploratory, and see what emerges. Rather than fitting a chosen case "
        "in advance, we let the stages and the parameter ranges run, look for where "
        "adoption shifts sharply or stalls, and let that point us toward the cases worth "
        "pursuing.")

    # ---- framing and approach -------------------------------------------
    doc.add_heading("Framing and approach", level=1)
    doc.add_paragraph(
        "Two kinds of result are what we are watching for. First, small changes in the "
        "underlying elements producing large, abrupt shifts in adoption, a prepared group "
        "flipping once the last piece arrives. Second, determined and well-resourced "
        "promotion failing to move adoption until those elements are in place, the "
        "familiar picture of a good idea that will not catch on no matter how hard it is "
        "pushed.")
    doc.add_paragraph(
        "The larger aim is to account for real diffusions that succeeded or failed in ways "
        "that simple and complex contagion cannot explain, since both of those move the "
        "whole package at once. Look-alike innovations with opposite fates, sudden mass "
        "shifts, and failed diffusion by fully-equipped promoters are the cases of "
        "interest.")

    doc.save(OUT)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    import sys
    # The shared .docx is the source of truth: edits and review comments live in it.
    # Refuse to clobber it unless regeneration is explicitly forced.
    if os.path.exists(OUT) and "--force" not in sys.argv:
        print(f"Refusing to overwrite {OUT}.")
        print("This .docx is the source of truth (manual edits and review comments "
              "live there). Pass --force only to regenerate from scratch and discard "
              "those edits.")
    else:
        build()
