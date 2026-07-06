---
title: "Spurious copper: acceptability and disposition criteria"
defect_class: spurious_copper
doc_type: acceptability
---
## Acceptability framework

An isolated copper island is judged on three questions: does it violate spacing, is it going anywhere (adhesion), and is it in a region where floating metal is prohibited? Product class (Class 1 consumer, Class 2 dedicated service, Class 3 high reliability) tightens each answer. These criteria are self-authored summaries of common industry practice, not reproductions of any copyrighted standard.

## Acceptable conditions

- The island is **solidly adhered** (no lifted edges, no flaking under a gentle probe), and
- The remaining clearance from the island's edge to every nearby conductor is at least the **design minimum spacing** — measured conductor-to-island, since the island shortens the isolation path in two steps, and
- The island lies outside regions the drawing flags as sensitive: high-voltage creepage paths, RF/microwave sections, high-impedance analog zones, and board-edge margins.

For general-purpose (Class 1/2-style) product, small well-adhered islands meeting the spacing test are routinely accepted and logged as **process indicators**. High-reliability (Class 3-style) programs commonly also cap the island's size and reject any island in a minimum-clearance channel even when spacing technically measures compliant, on the argument that margin — not just minimum — must be preserved.

## Defect (reject) conditions

- Clearance from the island to any adjacent conductor is **below the design minimum spacing**.
- The island shows **any lifted edge, flaking, or movement** under a gentle probe — mobile conductive debris is a latent short regardless of current spacing. Embedded drilling/routing swarf is treated this way by default, since its adhesion is untrusted.
- The island sits in a **prohibited zone**: high-voltage isolation gap, creepage/clearance path, RF structure keep-out, or any region where the drawing bans floating metal.
- The island's position or size makes post-assembly inspection impossible (e.g., it will hide under a BGA), and the program requires verifiable isolation there.

## Disposition guidance

Islands inside the acceptance limits ship as-is — scraping at a compliant, well-adhered patch risks gouging the laminate for no electrical gain. Islands outside the limits are strong rework candidates: removal is subtractive and low-risk under magnification (see the rework procedure for this class), and is broadly accepted across classes when documented. Because phototool spots print identical islands at the same coordinate on every board of a lot, one confirmed artwork-type island triggers a lot screen; scattered random islands instead point at resist development or etchant agitation, which is a process-engineering conversation rather than a board-by-board fix.
