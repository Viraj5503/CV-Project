---
title: "General inspection and acceptability concepts for bare PCBs"
defect_class: general
doc_type: acceptability
---
## Product classes and what they mean

Electronics acceptance criteria are conventionally organized into three product classes, tightening as the cost of failure rises. **Class 1** covers general consumer electronics, where the board must function but cosmetic imperfections and reduced margins are tolerated. **Class 2** covers dedicated-service equipment — telecom, industrial, instruments — where extended reliability is expected and uninterrupted service is desired but not safety-critical. **Class 3** covers high-reliability hardware — medical, aerospace, defense, safety systems — where the product must keep working and inspection criteria leave the most margin. The same physical condition can be acceptable in Class 1 and a reject in Class 3; a disposition is meaningless without knowing the class it was judged against. This knowledge base states criteria in this three-class style as self-authored summaries of common industry practice, without reproducing any copyrighted standard's text or tables.

## The three-way disposition

Mature inspection operations do not sort findings into just good and bad. Each observation lands in one of three buckets:

- **Acceptable** — the condition meets the class criteria; the board ships without action.
- **Process indicator** — the condition is within acceptance limits but shows the process drifting from its target (etch scallops, small well-adhered copper islands, minor registration offsets). The board ships, but the observation is logged and trended; recurring indicators trigger a process review at the fab.
- **Defect** — the condition violates the class criteria. The board is dispositioned: rework where an approved procedure exists, otherwise scrap or return to the fabricator.

Recording process indicators is what separates inspection from mere sorting — they are the early warning that the next lot will contain real defects.

## Measurements that drive bare-board dispositions

Most etched-pattern criteria reduce to a few recurring measurements: **remaining conductor width** at the worst point of any nick or bite, as a percentage of designed minimum width; **remaining clearance** between adjacent conductive features, against designed minimum spacing (measured through any intruding spur or island, since unwanted copper shortens the isolation path); **continuity and isolation**, verified electrically rather than visually for anything marginal; and **adhesion**, since partially attached copper is mobile debris regardless of today's geometry. Where a drawing defines explicit limits, the drawing wins over any generic criterion.

## Lot thinking

Bare-board defects are rarely one-board events. Phototool spots, drill-program omissions, and imaging voids repeat at identical coordinates on every board built from the same tooling; chemistry problems cluster by panel region. Every confirmed defect should therefore prompt two questions beyond this board's disposition: do lot siblings show the same condition at the same location, and does the lot's electrical test coverage catch what visual inspection might miss? A single accepted board from a bad lot is a warranty claim in transit.
