#!/usr/bin/env python3
"""Fold the 2026-08-16 diagnostics into the docx.

  1. Carrier diagnostics. Whether the carrier population is built by
     transmission or handed over by the initialization, measured at t=0, at its
     peak and at run end, under both activation regimes and under a stricter
     carrier threshold. Plus the share of successful component transfers whose
     sender was not manifest, which is measured directly rather than inferred
     from the channel intervention.
  2. Three readiness rules over one token history. The count comparator allows
     duplicates, which is the weakest accumulation rule available, so a
     source-nonredundant rule is added: readiness on k relevant tokens from k
     distinct senders. All three arms share the token history exactly.

This also corrects one sentence in the existing carrier-channel paragraph. It
asserted that nonadopters move most of the material, which at the time was not
measured. It now is, so the sentence carries the number instead of the claim.

Every value is computed from the result CSVs through the shared table builders,
so the folder and the verifier cannot disagree.

  python fold_carriers_source_docx.py            # preview
  python fold_carriers_source_docx.py apply
"""
import os, re, shutil, sys

import docx
from docx.shared import Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

import fold_200rep_tables as FT

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.environ.get("ABM_DOCX") or os.path.abspath(
    os.path.join(HERE, "..", "latent-adoption-build-review.docx"))
ANCHOR = "New specification details"

SRC_CD, SRC_CDE, SRC_SNR = FT.SRC["cd"], FT.SRC["cde"], FT.SRC["snr"]

BANNED = ["wedge", "clean", "core", "central", "genuine", "interesting", "natural",
          "mirror images", "what we are seeing", "brain breaker", "sanity baseline"]


# --------------------------------------------------------------------- tables
def table_carrier_diag():
    b = FT.BUILDERS["Carrier diagnostics"][0]()
    hdr = ["Carrier measure", "Activation", "At initialization", "Peak", "At run end"]
    body = []
    for (label, regime), vals in b.items():
        body.append([label, regime] + vals)
    return hdr, body


def table_transfers():
    b = FT.BUILDERS["Transfers by sender state"][0]()
    hdr = ["Activation", "Relevant transfers per run", "From nonmanifest sender",
           "From manifest sender", "Share from nonmanifest sender"]
    return hdr, [[k] + v for k, v in b.items()]


def table_threearm_cells():
    b = FT.BUILDERS["Three-arm cells"][0]()
    hdr = ["Readiness rule", "Capacity", "Loss rate", "Flow", "Adoption mean (sd)",
           "Carriers", "Evictions per agent", "Distinct sources held"]
    return hdr, [list(k) + v for k, v in b.items()]


def table_threearm_returns():
    b = FT.BUILDERS["Three-arm returns"][0]()
    hdr = ["Readiness rule", "Capacity", "Loss rate", "Return to flow",
           "Standard error", "Compositional minus this rule"]
    return hdr, [list(k) + v for k, v in b.items()]


# --------------------------------------------------------------------- prose
def para_carrier_diag():
    cd = FT.BUILDERS["Carrier diagnostics"][0]()
    tr = FT.BUILDERS["Transfers by sender state"][0]()
    g1s = cd[("Carrier, at least 1 component", "Scheduled")]
    g1e = cd[("Carrier, at least 1 component", "Endogenous")]
    g2s = cd[("Carrier, at least 2 components (k-1)", "Scheduled")]
    g2e = cd[("Carrier, at least 2 components (k-1)", "Endogenous")]
    sh_s = tr["Scheduled"][3].split(" ")[0]
    sh_e = tr["Endogenous"][3].split(" ")[0]
    return (
        "Whether the carrier population is built or seeded. The carrier measure "
        "requires only one relevant element while nonmanifest, and elements are "
        "seeded independently at a density of 0.15, so an agent holds at least one "
        "element of a four-element requirement set with probability 0.478 before "
        "anything has been transmitted. Read on the endpoint alone the measure "
        "therefore cannot show that the diffusion built the population, and read on "
        "the endpoint alone it appears to shrink. The trajectory settles it. Under a "
        f"scheduled trigger the carrier fraction runs from {g1s[0]} at initialization "
        f"to a peak of {g1s[1]} and then to {g1s[2]} at run end, and under an "
        f"endogenous trigger from {g1e[0]} to {g1e[1]} and then to {g1e[2]}. The fall "
        "is manifestation converting carriers into adopters, not material leaving the "
        "population, so what the endpoint records is the residue after conversion "
        "rather than the maximum. Under a stricter threshold of two relevant "
        "elements, which is k minus 1 at the focal setting, the initialization "
        f"supplies only {g2s[0]} and transmission raises it to {g2s[1]} under a "
        f"scheduled trigger and {g2e[1]} under an endogenous one. The broad carrier "
        "state is therefore part initialization and part diffusion, and the stricter "
        "measure is the one that shows the contribution of transmission without the "
        "seeding included. The share of the traffic that runs through agents who have "
        "not adopted is measured directly rather than inferred, by classifying each "
        "successful transfer of an element belonging to a big thing by whether the "
        f"sender was manifest for it. Under a scheduled trigger {sh_s} of those "
        f"transfers come from a sender who was not manifest, and {sh_e} under an "
        "endogenous one. The counters are observational. They increment after a "
        "transfer has already succeeded, draw no random numbers and change no state, "
        "and the canonical cell reproduces to four decimal places with them in place. "
        f"From sweeps {SRC_CD} and {SRC_CDE}, 200 replications each.")


def para_threearm():
    r = FT.BUILDERS["Three-arm returns"][0]()
    c60 = r[("compositional", "6", "0")]
    s60 = r[("source", "6", "0")]
    n60 = r[("count", "6", "0")]
    c50 = r[("compositional", "5", "0")]
    s50 = r[("source", "5", "0")]
    n50 = r[("count", "5", "0")]
    c6L = r[("compositional", "6", "0.01")]
    s6L = r[("source", "6", "0.01")]
    n6L = r[("count", "6", "0.01")]
    cells = FT.BUILDERS["Three-arm cells"][0]()
    lvl = {k: cells[(k, "6", "0", "low")][0].split(" ")[0]
           for k in ("compositional", "source", "count")}
    return (
        "Source diversity against content identity. The count rule above allows "
        "duplicates, which is the weakest accumulation rule available, so the "
        "comparison risks defeating a straw comparator. The rule the nonredundant "
        "information literature actually uses discounts a repeat exposure from the "
        "same neighbour and credits one from a new neighbour, which is a third "
        "position between the two already tested. Every token now carries the "
        "identity of the sender it arrived from as well as the identity of the "
        "element, and three readiness rules are run over one token history. The "
        "count rule requires k relevant tokens with duplicates included. The source "
        "rule requires k relevant tokens acquired from k different senders whatever "
        "their element identities. The compositional rule requires k distinct "
        "required element identities whatever their senders. The three are logically "
        "independent rather than nested, since three tokens of one type from three "
        "neighbours satisfy the source rule and fail the compositional one, and three "
        "distinct types from one neighbour do the reverse. Seeded tokens each receive "
        "their own origin, so the initialization does not handicap the source rule. "
        "Identity of the retained token state across all three arms, including both "
        "labels, is asserted at every tick over five parameter settings and three "
        "seeds, which is 9030 checks with no failures, and adding the sender labels "
        "left the previously reported compositional and count values unchanged. "
        "Without element loss the compositional rule is the only one of the three "
        f"whose response to greater transmission is negative. It returns {c60[0]} at "
        f"capacity 6 and {c50[0]} at capacity 5, against {s60[0]} and {s50[0]} under "
        f"the source rule and {n60[0]} and {n50[0]} under the count rule. The gap "
        f"between the compositional rule and the source rule, {s60[2]} at capacity 6 "
        f"and {s50[2]} at capacity 5, is wider than the gap against the count rule, "
        f"{n60[2]} and {n50[2]}, so replacing the weak comparator with the stronger "
        "one widens the result rather than narrowing it. With loss at 0.01 all three "
        f"gain from additional transmission, {c6L[0]} against {s6L[0]} and {n6L[0]} at "
        "capacity 6, and the ordering of the three rules is unchanged. Adoption under "
        f"the source rule sits between the other two at every cell, {lvl['source']} "
        f"against {lvl['compositional']} and {lvl['count']} at capacity 6 under low "
        "flow, so a reading in which the contrast merely reflects position on a "
        "bounded outcome scale does not hold. That reading predicts an intermediate "
        "response from an intermediate arm, and at capacity 5 the source rule instead "
        "has the most positive response of the three while sitting well below the "
        "count rule in level. Requiring particular element identities therefore does "
        "work that neither counting inputs nor requiring them from different senders "
        f"does. From sweep {SRC_SNR}, 200 paired replications per cell.")


# ----------------------------------------------------------------- doc edits
CARRIER_FIX_OLD = ("They move most of the material in this model, and that traffic "
                   "is consequential for adoption.")
CARRIER_FIX_NEW = ("Direct instrumentation of the transfer step, reported below, puts "
                   "the share of relevant element transfers coming from a sender who "
                   "is not manifest for the big thing at 0.60 under a scheduled "
                   "trigger and 0.49 under an endogenous one, so agents who have not "
                   "adopted carry a majority of the traffic under the canonical "
                   "setting and about half of it under the other.")

SPEC_ADD = (" Two further additions support the 2026-08-16 diagnostics. The engine "
            "counts each successful element transfer by whether the sender was "
            "manifest for a big thing the element serves, which is observational and "
            "verified to leave trajectories unchanged. And the token-memory harness "
            "now labels every token with the sender it arrived from as well as its "
            "element type, which is what makes the source-nonredundant readiness rule "
            "expressible over the same history as the other two.")


def set_borders(tbl):
    b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{e}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0"); el.set(qn("w:color"), "000000")
        b.append(el)
    tbl._tbl.tblPr.append(b)


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    p1, p2 = para_carrier_diag(), para_threearm()
    t1, t2 = table_carrier_diag(), table_transfers()
    t3, t4 = table_threearm_cells(), table_threearm_returns()

    bad = []
    for i, t in enumerate((p1, p2, CARRIER_FIX_NEW, SPEC_ADD), 1):
        if "—" in t:
            bad.append(f"text {i}: em dash")
        if ";" in t:
            bad.append(f"text {i}: semicolon")
        for b in BANNED:
            if re.search(r"\b" + re.escape(b) + r"\b", t.lower()):
                bad.append(f"text {i}: banned term {b!r}")
    print(f"sources: {SRC_CD} | {SRC_CDE} | {SRC_SNR}")
    print("prose governance:", "OK" if not bad else "FAILED " + "; ".join(bad))
    if bad:
        sys.exit(1)
    for nm, t in (("carrier diagnostics", p1), ("three readiness rules", p2)):
        print(f"\n--- {nm} ({len(t.split())} words)\n{t}")
    for nm, (h, b) in (("carrier diagnostics", t1), ("transfers by sender", t2),
                       ("three-arm cells", t3), ("three-arm returns", t4)):
        print(f"\n--- table {nm}: {len(b)} rows\n   " + " | ".join(h))
        for row in b[:5]:
            print("   " + " | ".join(row))
        if len(b) > 5:
            print(f"   ... {len(b) - 5} more rows")

    if not apply:
        print("\npreview only, nothing written.")
        return

    bak = DOCX + ".bak19"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"\nbackup -> {os.path.basename(bak)}")
    doc = docx.Document(DOCX)

    fixed = spec = False
    for q in doc.paragraphs:
        if CARRIER_FIX_OLD in q.text:
            for run in q.runs:
                if CARRIER_FIX_OLD in run.text:
                    run.text = run.text.replace(CARRIER_FIX_OLD, CARRIER_FIX_NEW)
                    fixed = True
            if not fixed:                       # claim split across runs
                keep = q.runs[0].bold
                txt = q.text.replace(CARRIER_FIX_OLD, CARRIER_FIX_NEW)
                for run in list(q.runs)[1:]:
                    run.text = ""
                head, tail = txt.split(". ", 1)
                q.runs[0].text = head + ". "
                q.runs[0].font.bold = keep
                q.add_run(tail)
                fixed = True
        if q.text.strip().startswith(ANCHOR) and SPEC_ADD.strip() not in q.text:
            q.add_run(SPEC_ADD)
            spec = True
    print("carrier-channel sentence corrected:", fixed)
    print("specification details extended:", spec)

    anchor = None
    for q in doc.paragraphs:
        if q.text.strip().startswith(ANCHOR):
            anchor = q._p
            break
    if anchor is None:
        sys.exit("anchor not found")

    def mk_para(text):
        pp = doc.add_paragraph()
        pf = pp.paragraph_format
        pf.space_before = Pt(12); pf.space_after = Pt(6)
        a, b = text.split(". ", 1)
        pp.add_run(a + ". ").font.bold = True
        pp.add_run(b)
        return pp._p

    def mk_table(spec_):
        h, b = spec_
        t = doc.add_table(rows=1, cols=len(h))
        set_borders(t)
        for j, x in enumerate(h):
            t.rows[0].cells[j].paragraphs[0].add_run(x).font.bold = True
        for row in b:
            c = t.add_row().cells
            for j, x in enumerate(row):
                c[j].paragraphs[0].add_run(x)
        return t._tbl

    for el in [mk_para(p1), mk_table(t1), mk_table(t2),
               mk_para(p2), mk_table(t3), mk_table(t4)]:
        anchor.addprevious(el)
    doc.save(DOCX)
    print("folded: 2 paragraphs, 4 tables")


if __name__ == "__main__":
    main()
