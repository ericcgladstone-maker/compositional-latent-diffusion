# Why this contrast is not usable, and what would be needed instead

Run: `explore_contagion_contrast.py`, 200 replications, 2026-08-14.
**These results are deliberately NOT folded into the build document.** The CSVs
are kept so the attempt is on the record and nobody repeats it.

## What it was for

An equipped, manifest minority failing to move adoption does not on its own
separate this model from contagion: complex contagion predicts the same thing
whenever seeds sit below the reinforcement threshold. The intent was to concede
that overlap and then show what does differ, namely that composition produces a
population holding SOME of what is needed while contagion cannot.

## Why it does not work

**1. Partial holding is not exclusive to composition.** When capacity cannot
hold the full required set, a whole-package transfer is truncated and the
receiver ends up holding part of it. At capacity 3 with a requirement of 4, the
whole-package arm gives a partial-holder fraction of 1.00, identical to
piecemeal. The measure does not identify the mechanism it was meant to identify.

**2. The zero-density cells are arithmetic artifacts.** With no ambient
elements only one of the two big things is ever seeded. It reaches 1.00, the
other stays at 0.00, and the reported share averages the two, which is where the
exactly 0.5000 values come from. The partial-holder figure of exactly 0.5000 has
a second cause: the two big things share an element, so every agent who fully
adopted the first counts as a partial holder of the second.

**3. The contagion arms sit at their ceiling.** Adoption reaches 0.998 with and
without the minority, so "no lift here either" carries no information about the
minority. A comparison needs the arms to be off their ceilings.

Every regime probed collapsed one way or the other: adoption near zero with
everyone a partial holder, or adoption near one with nobody a partial holder.

## What is usable

The `density 0.05` rows record adoption with and without the minority in each
arm and are internally consistent. They are not evidence about mechanism.

The discriminating measurement the build already has is the carrier fraction in
the W3 analysis, 0.35 under piecemeal transmission against 0.01 under
whole-package, measured where capacity exceeds the requirement so the truncation
confound above does not apply.

## What a real comparison would need

- Arms matched on adoption level rather than run at their own ceilings, so the
  seeded minority has comparable room to act in each.
- A discriminating measure that truncation cannot produce. Candidates: the
  distribution of held fraction among non-adopters over time rather than at the
  end, or the rate at which an agent acquires and loses individual elements,
  which has no analogue where the object moves as a unit.
- Alternatives fitted to generated curves rather than compared at one operating
  point, which is the parsimony test that has been open since June.

This is a design problem, not a tuning problem, and it should be designed
deliberately rather than assembled from the parts that happened to be at hand.
