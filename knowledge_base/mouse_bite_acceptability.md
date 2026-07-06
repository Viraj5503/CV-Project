---
title: "Mouse bite: acceptability and disposition criteria"
defect_class: mouse_bite
doc_type: acceptability
---
## Acceptability framework

Edge nicks in conductors are judged by how much of the designed conductor cross-section survives at the worst point. The criteria below summarize widely applied industry practice in the three-class style (Class 1 general consumer, Class 2 dedicated service, Class 3 high reliability); they are self-authored for this knowledge base and are not reproductions of any copyrighted standard. The controlling measurement is remaining conductor width at the deepest bite, expressed as a percentage of the **minimum designed width** for that conductor.

## Acceptable conditions

- The bite is isolated (not a chain of overlapping notches) and the remaining conductor width at the narrowest point is at least **80% of the designed width** for high-reliability (Class 3 style) product, or at least **70%** for general-purpose (Class 1/2 style) product.
- The notch does not expose or undercut adjacent features and there is no cracking visible at the notch root under magnification.
- The affected conductor is not a controlled-impedance line, a current-critical power path, or otherwise flagged in the drawing as non-reducible.

Findings inside these limits are best logged as **process indicators**: acceptable on this board, but evidence that etch or imaging control is drifting and worth a process review if they recur.

## Defect (reject) conditions

- Remaining width at the narrowest point is below the class limit above.
- Multiple bites cluster so their effects combine — several notches within a short span of trace should be evaluated as one long reduction, not judged individually.
- Any crack, tear, or lifted copper is visible at the notch, since these propagate under thermal or mechanical stress.
- The bite sits on a conductor the design marks as critical (power feed, impedance-controlled, fine-pitch escape), regardless of percentage.

## Disposition guidance

Boards inside the limits ship without rework — adding solder or other material to a compliant notch creates more risk than it removes. Boards outside the limits on non-critical nets may be candidates for documented repair (bridging the weakened neck; see the rework procedure for this class), typically defensible for Class 1/2-style product only. For high-reliability product, width reductions beyond the limit are normally scrapped or returned to the fabricator rather than repaired, and a lot-level etch-process review should be requested since mouse bites rarely occur on a single board alone.
