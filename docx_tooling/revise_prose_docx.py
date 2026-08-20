#!/usr/bin/env python3
"""Style revision of the master docx per the co-author style guide.

Removes performative / slogan / self-adjudicating prose. Preserves ALL numbers,
sweep ids, parameter values, defaults, run counts, SDs, stage labels, caveats,
bug notes, and exploratory markers. No em dashes, no semicolons. Edits prose
paragraphs (bold lead-in preserved) and targeted table-cell phrases (substring
swaps that leave numbers untouched). Comment anchors are preserved.
"""

import os, shutil
import docx
from docx.oxml.ns import qn

HERE = os.path.dirname(os.path.abspath(__file__))
DOCX = os.path.abspath(os.path.join(HERE, "..", "latent-adoption-build-review.docx"))

# (match_prefix, bold_lead_or_empty, body)
PROSE = [
 ("The build is progressive rather than fully crossed", "",
  "The build is progressive rather than fully crossed. A fully crossed design is not used "
  "because the mechanism set is built up one component at a time. Each stage adds one "
  "component to the stage before it and serves as its control, and within a stage a single "
  "factor is varied across its range while the rest are held fixed."),
 ("Before any results, the build is verified", "",
  "Before any results, the build is verified at two levels: each parameter and mechanism is "
  "driven directly and checked against its description, and the whole model is run end to end "
  "under structural invariants. The table summarizes what was confirmed. One bug surfaced "
  "this way: reversible adoption was not activating because a manifest node was reported as "
  "fully realized. This was fixed. The audit is designed to detect implementation failures."),
 ("Baseline. With no binding capacity", "Baseline. ",
  "With no binding capacity constraint, every seeding density drives adoption to full "
  "saturation. Final adoption is 1.00 across the entire range of initial element density, "
  "with zero overshoot and zero lapse. This stage is the null condition. Constrained dynamics "
  "do not appear until a capacity constraint is introduced, so this stage is the reference for "
  "the later stages."),
 ("Limited attention. Capacity relative", "Limited attention. ",
  "Capacity relative to assembly requirements produces a capacity-threshold transition. "
  "Adoption rises from 0.11 under the tightest cap to 1.00 once the constraint loosens. The "
  "lapse rate follows the same structure, reaching 0.35 under tight capacity and falling to "
  "near zero at saturation."),
 ("Whole versus piecemeal transmission", "Whole versus piecemeal transmission. ",
  "This comparison isolates the adoption gap between transmitting a complete package and "
  "transmitting only its constituent elements. Whole-package transmission produces "
  "near-saturation. Elements-only transmission produces slower, stepwise adoption because "
  "elements must accumulate before manifestation. Elements-only transmission also produces "
  "more churn than whole-package transmission, a second difference between the two "
  "specifications."),
 ("Note on churn", "Churn under whole-package and elements-only transmission. ",
  "Whole-package transmission shows near zero overshoot and a lapse rate of 0.57. In the "
  "aggregate, adoption saturates and remains saturated while individual nodes drop below "
  "threshold and re-acquire the package. Elements-only transmission shows a lapse rate of "
  "0.24 with net erosion measured as overshoot of 0.13. Whole-package transmission is a "
  "high-turnover equilibrium at saturation. Elements-only transmission erodes from its peak."),
 ("Closer look, the observability gap", "Observability gap. ",
  "Tracking the substrate held (big-thing elements present in the population) against manifest "
  "adoption over time shows where the two transmissibility modes differ. Until the first "
  "trigger the modes are identical, with the substrate rising to about 0.60 while adoption "
  "stays at zero, the latent build-up implied by the model. After the trigger the sign of the "
  "observability gap reverses between the two modes. Under elements-only transmission the "
  "substrate continues to lead adoption, a positive gap near 0.09. Under whole-package "
  "transmission adoption exceeds the substrate, a negative gap near -0.17, because the "
  "manifest state is transmitted and a node can be manifest without holding the full element "
  "set. These trajectories come from a follow-up run at the same operating point, sweep "
  "20260623-144801, 30 replications."),
 ("Add-on: differential slot cost", "Add-on: differential slot cost. ",
  "Charging a large package two capacity slots rather than one increases the same "
  "capacity-driven competition seen under limited attention. Adoption rises from 0.32 at the "
  "tightest capacity to 0.99 once capacity is ample. Overshoot and lapse stay at zero across "
  "the sweep, so the change rescales slot competition without introducing a new dynamic."),
 ("Add-on: compression", "Add-on: compression. ",
  "Endpoint adoption is nearly flat across the parameter sweep, and overshoot approaches zero. "
  "A chunked adopter cannot lapse, so compression reduces churn while endpoint adoption "
  "changes little across the sweep."),
 ("Add-on: stabilization. Protecting", "Add-on: stabilization. ",
  "Protecting adopted elements from loss reduces overshoot to approximately 0.05 and sustains "
  "adoption under churn. The effect scales with stabilization strength: adoption falls from "
  "0.87 under full protection to 0.27 with no protection."),
 ("Add-on: enhanced transmission", "Add-on: enhanced transmission. ",
  "Final adoption is approximately flat, and overshoot rises to 0.21, among the higher values "
  "in the sweep. Enhanced transmission accelerates initial adoption, and those gains then "
  "erode. Enhanced transmission changes the trajectory more than the endpoint."),
 ("Add-on: stabilization with enhanced", "Add-on: stabilization with enhanced transmission. ",
  "With both add-ons active, increasing the enhanced factor raises adoption from 0.39 to 0.66, "
  "and the lapse rate rises from 0.40 to 0.56. Stabilization retains enough of each gain for "
  "higher transmission to accumulate. Neither mechanism produces this increase alone."),
 ("Add-on: tie strength channels", "Add-on: tie strength channels. ",
  "Adoption increases monotonically as the strong-tie fraction rises, from 0.51 with no strong "
  "ties to 0.73 when three in ten ties are strong. Churn stays low throughout, with overshoot "
  "no higher than 0.02. Strong ties concentrate repeated contact between the same agents, "
  "which supports assembly of the required element set."),
 ("Add-on: internal coupling", "Add-on: internal coupling. ",
  "The relationship is non-monotonic, with adoption peaking at coupling -0.5. The effect "
  "operates through churn when adoption is reversible and disappears when reversibility is "
  "disabled, where adoption remains near 0.91. The -1 endpoint reflects a separate "
  "clip-induced lock-in and not the same coupling mechanism."),
 ("Add-on: neighbor coupling", "Add-on: neighbor coupling. ",
  "Negative neighbor coupling increases adoption and positive neighbor coupling reduces it. In "
  "this specification the direction follows from suppression of cross-target competitors, "
  "confirmed by disabling the same-target term. The same-target term adds a complex-contagion "
  "effect at the negative end of the parameter range."),
 ("Add-on: content-specific incompatibility", "Add-on: content-specific incompatibility. ",
  "Making large packages mutually exclusive reduces adoption from 0.65 to 0.44 because each "
  "node can hold at most one package. Content-specific incompatibility is an explicit "
  "exclusivity mechanism, separate from capacity limits and from the coupling endpoint."),
 ("Evangelists in an unready population", "Evangelists in an unready population. ",
  "Increasing the number of evangelists has little effect on adoption. In the evangelist "
  "condition adoption remains nearly flat because manifest agents transmit constituent "
  "elements rather than the assembled package. The elements must then reassemble within the "
  "target population."),
 ("What we are seeing", "Recurring model signatures", ""),
 ("Across the stage analyses", "",
  "Across the stage analyses, four recurring patterns follow from the same model distinction: "
  "elements are transmitted, while adoption requires assembly into a larger configuration."),
 ("Core premise", "Level separation between transmission and adoption", ""),
 ("The transmitted object is not the adopted object", "",
  "The transmitted object is not the adopted object. Elements are transmitted, and adoption "
  "occurs only when elements form a larger configuration. In models where the transmitted "
  "object and the adopted object are the same, exposure can increase adoption directly. In "
  "this model, transmitted elements must be retained and assembled before adoption occurs. "
  "This level separation produces prolonged inertia, threshold-like transitions, recurrent "
  "lapse, and reduced diffusion in the evangelist condition, without a separate mechanism for "
  "each pattern."),
 ("Compression converts an assembled set", "",
  "Compression converts an assembled set of elements into a single chunk. Once compressed, the "
  "configuration no longer disintegrates through component loss, and it is no longer "
  "transmitted as separable pieces. Compression therefore stabilizes adoption within the "
  "holder and reduces the holder's capacity to reproduce the acquisition process in others."),
 ("The visible trigger receives causal credit", "",
  "A visible trigger can appear to explain abrupt adoption, but manifestation depends on prior "
  "accumulation and retention of the required elements. The trigger acts on a prepared state "
  "and is not the source of the accumulated elements. In this model, the same cue produces "
  "different outcomes across populations with different levels of latent readiness."),
 ("Robustness across structural variation", "Robustness across structural variation. ",
  "The adoption gap (whole-package adoption minus elements-only adoption) stays positive "
  "across every structural setting tested: topology, mean degree, population size, seeding "
  "density, transmission probability, and assembly difficulty, ranging about +0.18 to +0.62. "
  "Whole-package transmission does not always saturate. Where assembly is hard, both modes "
  "fall, and the gap does not close. The positive gap across the tested settings indicates "
  "that the separation is not specific to the default parameter setting. From sweep "
  "20260623-144801, 30 replications."),
 ("Three sources of the wedge", "Three contributions to the adoption gap. ",
  "The gap has three contributing barriers: assembly of multiple elements into a set, "
  "activation of a held substrate by a trigger, and competition for capacity among element "
  "types. Each barrier alone produces a gap. The gap reaches zero only when assembly, "
  "triggering, and capacity competition are all removed in the tested sweep. From sweep "
  "20260623-144801."),
]

TABLE_SUBS = [
 (" where the interesting inertia lives", ""),
 (", whereas synchronous updates", ", and synchronous updates"),
 (" (the invisible becomes visible)", ""),
 ("a clean alternative to driving coupling to its -1 floor",
  "a more direct alternative to driving coupling to its -1 endpoint"),
 ("(produces the failed-diffusion signature)", "(produces the evangelist condition)"),
 ("If content-specific exclusivity proves important, it is better modeled",
  "If content-specific exclusivity is needed, it is better modeled"),
 ("A sanity baseline, so that any later structure can be attributed to the limits rather than to the machinery.",
  "A baseline condition, so that any later structure can be attributed to the capacity limits and not to the model components."),
 ("The failed-diffusion case: a determined push that still cannot move adoption until the pieces themselves spread.",
  "The evangelist condition: an equipped, manifest minority that does not raise adoption until the constituent elements spread."),
 ("so the machinery works and later structure comes from the limits, not a defect.",
  "so the model components work and later structure comes from the limits and not from a defect."),
 ("Why canonical contagion or diffusion models do not generate it naturally",
  "Why models that identify transmission with adoption do not generate it"),
 ("The staircase under piecemeal transmission", "Stepwise adoption under piecemeal transmission"),
 ("This is the core result.", "This is the capacity-threshold result."),
 ("Canonical models typically produce smooth diffusion curves because the adopted object is also the transmitted object. They do not require dispersed components to accumulate and assemble before adoption occurs.",
  "In models where the transmitted object and the adopted object are the same, exposure can increase adoption directly. In this model, dispersed elements must accumulate and assemble before adoption occurs."),
 ("Standard contagion generally approaches an absorbing or stable state. It does not produce repeated adoption and lapse unless loss, decay, or reversal is added separately.",
  "Repeated adoption and lapse require an explicit reversibility, loss, or decay process in standard contagion formulations. Here, lapse follows from reversible adoption under capacity-constrained element retention."),
 ("In standard diffusion, additional adopters expand the set of transmission sources. Here, evangelists transmit components rather than the assembled package, so additional sources need not increase package-level adoption.",
  "Additional manifest adopters do not necessarily increase package-level adoption because they transmit elements rather than the assembled package."),
 ("Standard exposure models treat receipt of the transmissible object as sufficient for possible adoption. They do not distinguish exposure from the capacity to retain and assemble its components.",
  "Models that treat receipt of the transmissible object as sufficient for adoption do not distinguish exposure from the retention and assembly of components."),
]


def content_runs(p):
    return [r for r in p.runs if r.text]


def set_para(p, lead, body):
    runs = content_runs(p)
    if not runs:
        return False
    bold = [r for r in runs if r.bold]
    norm = [r for r in runs if not r.bold]
    # Clear EVERY text node in the paragraph first (catches runs python-docx's
    # p.runs may not expose, e.g. nested), so no old text can survive. Comment
    # markers (commentRangeStart/End, commentReference) carry no w:t and are
    # left untouched.
    for t in p._p.iter(qn("w:t")):
        t.text = ""
    if lead and bold:
        bold[0].text = lead
        if norm:
            norm[0].text = body
        elif body:
            p.add_run(body)
    else:
        full = (lead + body).strip() if lead else body
        runs[0].text = full
    return True


def main():
    bak = DOCX + ".bak3"
    if not os.path.exists(bak):
        shutil.copy2(DOCX, bak)
        print(f"backup -> {bak}")
    doc = docx.Document(DOCX)

    # prose
    applied = 0
    for prefix, lead, body in PROSE:
        hit = None
        for p in doc.paragraphs:
            if p.text.strip().startswith(prefix):
                hit = p
                break
        if hit is None:
            print(f"  PROSE MISS: {prefix!r}")
            continue
        set_para(hit, lead, body)
        applied += 1
    print(f"prose paragraphs revised: {applied}/{len(PROSE)}")

    # table cells
    sub_counts = {a: 0 for a, _ in TABLE_SUBS}
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    runs = content_runs(p)
                    if not runs:
                        continue
                    full = "".join(r.text for r in runs)
                    new = full
                    for a, b in TABLE_SUBS:
                        if a in new:
                            new = new.replace(a, b)
                            sub_counts[a] += 1
                    if new != full:
                        runs[0].text = new
                        for r in runs[1:]:
                            r.text = ""
    print("table substitutions applied:")
    for a, c in sub_counts.items():
        print(f"  {c}x  {a[:55]!r}")
    missed = [a for a, c in sub_counts.items() if c == 0]
    if missed:
        print(f"  WARNING {len(missed)} substitution(s) never matched")

    doc.save(DOCX)
    print("saved.")


if __name__ == "__main__":
    main()
