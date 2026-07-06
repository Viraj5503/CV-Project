---
title: "Spur: acceptability and disposition criteria"
defect_class: spur
doc_type: acceptability
---
## Acceptability framework

Spurs are judged by what they do to electrical clearance: the controlling measurement is the remaining gap between the spur tip and the nearest adjacent conductor, compared with the **minimum designed spacing** for that region. The class system applies in the usual way (Class 1 consumer, Class 2 dedicated service, Class 3 high reliability), tightening how much intrusion is tolerated. These criteria are self-authored summaries of common industry practice, not reproductions of any copyrighted standard.

## Acceptable conditions

- The spur is solidly attached (no thin hinge neck), blunt rather than filament-like, and the remaining clearance to the nearest conductor is at least the **design minimum spacing** — the spur consumes only spare clearance beyond the required gap.
- For general-purpose (Class 1/2-style) work, a common shop criterion also accepts spurs that intrude into surplus spacing by up to **30% of the actual gap**, provided the design minimum is still met; high-reliability (Class 3-style) work typically allows no measurable intrusion below the design minimum plus margin.
- The spur sits away from high-voltage clearances, board edges, and connector fields, where spacing requirements carry safety margins.

Spurs inside these limits should still be logged as **process indicators**: they are artwork or etch signatures that repeat across a lot, and recurring spurs at one coordinate mean a phototool or resist problem worth fixing at the source.

## Defect (reject) conditions

- Remaining clearance from spur tip to the adjacent conductor is **below the design minimum spacing** — this is a spacing violation regardless of how the copper got there.
- The spur physically touches the neighboring conductor: that is a short, dispositioned under short-circuit criteria.
- The spur is a long filament or has a visibly thin attachment neck — breakage risk makes it a defect even when current clearance measures acceptable.
- The spur is in a high-voltage isolation region, creepage path, or safety-spacing zone defined in the drawing, regardless of measured gap.

## Disposition guidance

Spurs outside the limits are excellent rework candidates: removal is a simple subtractive trim with low risk when done under magnification (see the rework procedure for this class). Trimming is broadly accepted even for higher-class product because it restores the as-designed geometry without adding material — though Class 3-style programs still require the repair to be documented and re-inspected. After trimming, verify the same coordinate on lot siblings: artwork-driven spurs repeat identically across every board imaged from the same tool.
