---
title: "General rework practices and workstation discipline"
defect_class: general
doc_type: rework
---
## Before touching the board

Rework begins with paperwork, not a blade. Confirm the finding is a genuine defect against the **current** design data — artwork revision, netlist, drill drawing — because intentional features (net ties, thieving pads, spark gaps, revision changes) regularly masquerade as defects against stale overlays. Confirm an approved rework procedure exists for the defect type and the product class; high-reliability programs typically require explicit engineering or customer authorization before any conductor-level repair. And decide up front what "verified" will mean afterward: which continuity, isolation, or dimensional checks prove the repair, and where it is recorded.

## Workstation discipline

- **ESD control**: grounded wrist strap, dissipative mat, and grounded tools whenever handling boards — a repair that silently kills a component elsewhere is worse than the original defect.
- **Magnification and light**: conductor-level work is done under a stereo microscope or bench magnifier (10x or better) with oblique lighting; if you cannot see the whole defect and its neighborhood at once, do not cut.
- **Cleanliness**: isopropyl alcohol and lint-free wipes before and after; flux residue and copper swarf left behind become tomorrow's leakage path or short. Removed metal goes onto tape immediately — a copper sliver lost on the board surface is a latent failure at a random coordinate.
- **Heat management**: use a temperature-controlled iron at the lowest effective setting with fresh flux; excess dwell lifts pads and delaminates traces. Two clean seconds beat ten hesitant ones.
- **Anchor your hands**: bladework is done with the hand braced on the bench or fixture, cutting away from healthy conductors, in light passes. The most common rework injury to a board is the slip that converts one defect into two.

## The repair hierarchy

Prefer the least invasive technique that restores compliance: subtractive repairs (trimming a spur, shaving a bridge, lifting an island) are more reliable than additive ones (solder reinforcement, wire straps, jumpers), and additive repairs on the original route beat re-routing through jumper wires. Never rework a finding that is within acceptance limits — a compliant board leaving the station worse than it arrived is the definition of overprocessing. When a repair attempt starts consuming healthy material (gouged laminate, nicked neighbors), stop and return the board to disposition rather than compounding.

## Verification and records

Every conductor repair is verified electrically, not just visually: continuity along the repaired net, isolation to adjacent nets, and the board's standard electrical test before release. The rework record captures location, defect, technique, materials, measurements, operator, and date — both for traceability and because repeated rework at the same coordinate across boards is a process signal the fabricator needs. Most programs also cap how many times one location may be reworked; heat and mechanical stress accumulate, and the second repair of a site starts from weaker material than the first.
