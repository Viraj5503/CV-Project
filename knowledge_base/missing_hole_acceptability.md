---
title: "Missing hole: acceptability and disposition criteria"
defect_class: missing_hole
doc_type: acceptability
---
## Acceptability framework

Bare-board acceptance is commonly judged against three product classes, in the style used across the electronics industry: Class 1 covers general consumer products where cosmetic imperfections are tolerated, Class 2 covers dedicated-service equipment where extended reliability is expected, and Class 3 covers high-reliability products — medical, aerospace, safety systems — where continued performance is critical and criteria are strictest. The criteria below are self-authored summaries of widely applied industry practice, not reproductions of any copyrighted standard.

## Acceptable conditions

There is essentially no product class in which a truly missing hole is acceptable, because the defect defeats either assembly or electrical connectivity. The only situations that look like a missing hole but may be accepted are documentation mismatches: a hole intentionally removed in a design revision but still shown on outdated inspection overlays, or an unplated tooling hole that a particular assembly does not use. Both are resolved by verifying against the current drill drawing rather than by accepting the board as-is.

## Defect (reject) conditions

Treat the board as nonconforming when any of the following holds:

- A component hole called out in the current drill data is absent — the part cannot be assembled.
- A via required for interlayer connection is absent — the affected net is electrically open, even if all surface traces appear intact.
- A mounting, registration, or tooling hole required by the assembly process is absent.

Because missing holes stem from systematic drilling faults, a confirmed missing hole on one board is grounds for screening the entire lot: check the same coordinate on every board from the panel or production run before dispositioning any of them individually.

## Disposition guidance

For plated through-holes, the practical disposition is reject and return to the fabricator, because a compliant plated barrel cannot be created outside the plating line — drilling a new hole in the field leaves bare, unplated walls with no interlayer connection. Field rework is defensible only in narrow cases: a missing **non-plated** mechanical hole on a low-class board may be drilled by a qualified operator with proper fixturing, and a missing via's connectivity can sometimes be restored with a surface jumper wire when the design allows. Any such rework must be documented, electrically verified, and approved for the product class; for Class 3 hardware, missing holes should be dispositioned by the fabricator, not repaired locally.
