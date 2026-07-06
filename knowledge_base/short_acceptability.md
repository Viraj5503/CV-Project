---
title: "Short circuit: acceptability and disposition criteria"
defect_class: short
doc_type: acceptability
---
## Acceptability framework

Isolation between nets, like continuity along them, is a functional requirement: the product class (Class 1 consumer, Class 2 dedicated service, Class 3 high reliability) governs what corrective action is allowed, not whether a bridge between nets is a defect. These criteria are self-authored summaries of common industry practice, not reproductions of any copyrighted standard.

## Acceptable conditions

None for a true short — copper connecting two distinct nets is a defect in every class. Rule out the look-alikes against design data before writing the finding:

- **Intentional copper** — net ties, shorting links, guard pours, and thermal spokes connect features by design. Verify against the current artwork and netlist, not an inspection overlay that may be stale.
- **Same-net adjacency** — a bridge between two features of the same net (e.g., a trace and its own pour) is electrically harmless; it may still be logged as a process indicator because the etch left copper the artwork does not show.
- **Surface debris** — a loose metallic particle sitting in the clearance is foreign material, not an etched short; it is removed by cleaning and dispositioned under cleanliness criteria.

## Defect (reject) conditions

- Any copper path, of any width, connecting two different nets — including high-resistance filaments that read kilo-ohms rather than zero. A measurable leakage path below the design's isolation requirement is a short.
- A copper sliver lying loose or partially attached within the clearance gap, even if isolation currently measures good: vibration or reflow can move it into contact.
- Clearance between adjacent features reduced below the design minimum by a protrusion that does not yet touch — dispositioned under spur/spacing criteria, but flagged here because marginal clearances and shorts share root causes.

## Disposition guidance

A confirmed short is rejected; the practical decision is rework-versus-scrap. Bridges on outer layers are usually removable by a trained operator (see the rework procedure for this class), and such repairs are broadly accepted for Class 1/2-style product when documented and re-tested. Inner-layer shorts cannot be reached and mean scrap or return to the fabricator. For Class 3-style hardware, even outer-layer bridge removal generally requires explicit engineering or customer authorization. After any confirmed short: verify the same coordinates on lot siblings (tool-driven causes repeat), and confirm the lot has electrical isolation test coverage before shipment — visual inspection alone does not catch filament shorts.
