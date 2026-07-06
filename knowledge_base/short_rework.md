---
title: "Short circuit: rework and repair procedure"
defect_class: short
doc_type: rework
---
## Repair feasibility

Outer-layer shorts are usually repairable: the offending copper is accessible and the repair is subtractive — remove the bridge, verify isolation, reseal. Success depends on geometry: a discrete web or sliver between two features is straightforward, while a large under-etched region merging several conductors may leave too little healthy clearance to restore and can push the board to scrap. Inner-layer shorts are not field-repairable. Removal is done mechanically with a blade or micro-abrasion; on dense fine-pitch areas, the working rule is that the cure must not cost more copper than the disease — nicking adjacent conductors while cutting a bridge trades a short for an open.

## Tools and materials

- Stereo microscope (10x or better) with oblique lighting; the bridge must be fully visible before any cutting
- Curved scalpel / sharp knife blade, or a fine rotary micro-abrasion tool for larger webs
- Fiberglass scratch brush for cleanup, IPA and lint-free wipes
- Multimeter for isolation verification (and the netlist, to know which nets to probe)
- Repair-grade solder mask or conformal lacquer for resealing

## Procedure

1. **Map the bridge**: under magnification, trace the full extent of the unwanted copper and identify the two nets involved from the netlist. Measure isolation before rework to establish the baseline (a filament short may read ohms to kilo-ohms).
2. **Remove mask locally**: if the bridge hides under solder mask, scrape the mask back until the entire bridge and the clearance channel around it are exposed.
3. **Cut the bridge**: with the blade held perpendicular to the bridge and away from adjacent conductors, shave the unwanted copper in light passes until laminate shows across the full designed clearance channel. For wide webs, use micro-abrasion and finish the edges with the blade. Never lever the blade under healthy traces.
4. **Clear the debris**: brush out copper swarf with the fiberglass brush and clean with IPA — a conductive shaving left in the channel recreates the defect.
5. **Verify isolation**: measure resistance between the two nets; it must meet the design's isolation requirement (typically effectively open at multimeter scale). Also verify continuity along both nets to confirm no adjacent conductor was nicked.
6. **Reseal**: re-cover the exposed area with repair mask or lacquer to restore the original insulation and protect the cleaned clearance.

## Post-repair inspection

Inspect under magnification for full clearance restoration, clean channel walls, and undamaged neighbors; confirm both electrical checks (isolation between the nets, continuity along each). Record location, nets, removal method, measurements, operator, and date in the rework log. Route the board through standard electrical test before release, and trigger a lot screen at the same coordinates — etch and artwork causes repeat across boards.
