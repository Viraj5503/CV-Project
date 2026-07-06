---
title: "Spur: rework and repair procedure"
defect_class: spur
doc_type: rework
---
## Repair feasibility

Spur removal is one of the most reliable PCB repairs: the defect is unwanted material, the fix is subtractive, and nothing needs to be added or reflowed. The spur is trimmed back to the parent conductor's designed outline, restoring the clearance gap. The only real risks are collateral — gouging the parent trace at the attachment point, nicking the adjacent conductor the spur points at, or leaving the severed copper filament on the board as conductive debris. All three are controlled by magnification, light cuts, and cleanup.

## Tools and materials

- Stereo microscope or bench magnifier (10x or better) with oblique lighting
- Curved scalpel or fine flat blade; fine tweezers for removing the severed filament
- Fiberglass scratch brush, isopropyl alcohol, lint-free wipes
- Multimeter for post-trim verification on tight clearances
- Repair-grade solder mask or conformal lacquer if mask was opened

## Procedure

1. **Measure first**: record the clearance from spur tip to the adjacent conductor and check the acceptability criteria — a spur inside limits is logged as a process indicator, not trimmed.
2. **Expose the site**: if the spur is under solder mask, scrape the mask back just enough to see the entire spur and the clearance channel around it.
3. **Trim the spur**: anchor your hand, place the blade flat against the parent conductor's designed edge, and shave the spur off in light passes, cutting **away from** the adjacent conductor. Blunt the attachment point flush with the feature outline — do not dig into the parent trace.
4. **Capture the debris**: lift the severed filament with tweezers immediately; a loose copper whisker left on the board is a future short. Brush and IPA-clean the area.
5. **Verify**: under magnification, confirm the feature edge is restored and the full designed clearance is open. On fine-pitch or high-voltage regions, measure isolation between the two nets with a multimeter.
6. **Reseal**: if mask was removed, re-cover the area with repair mask or lacquer.

## Post-repair inspection

Confirm the parent conductor's width was not reduced at the attachment point (if the blade bit in, evaluate the nick under conductor-width criteria as a mouse-bite-type reduction). Verify clearance meets the design minimum, verify no debris remains, and log the location, measurements, operator, and date. Because spurs are usually artwork or resist signatures, request a check of the same coordinate on other boards of the lot — trimming one board does not fix the phototool that printed it.
