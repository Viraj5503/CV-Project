---
title: "Open circuit: acceptability and disposition criteria"
defect_class: open_circuit
doc_type: acceptability
---
## Acceptability framework

Conductor continuity is a functional requirement, not a cosmetic one, so the class system (Class 1 general consumer, Class 2 dedicated service, Class 3 high reliability) does not change **whether** an open is a defect — it changes **what may be done about it**. The criteria here are self-authored summaries of standard industry practice, not reproductions of any copyrighted standard.

## Acceptable conditions

None. A broken conductor is a defect in every class of product. Two look-alike situations are worth ruling out before writing the finding, both resolved against design data rather than by accepting a break:

- **Intentional gaps** — spark-gap features, unpopulated option links, or nets legitimately split in a design revision can look like breaks against an outdated overlay. Verify against the current artwork and netlist.
- **Mask-covered narrow necks** — solder mask pooling can visually mimic a gap on a continuous trace. Confirm with electrical continuity before condemning the trace.

## Defect (reject) conditions

- Any complete separation of a conductor, of any length, on any net — including hairline fractures that show continuity intermittently. An intermittent open is treated as an open.
- Any open barrel or missing interlayer connection presenting as an open on the net (dispositioned with via/hole criteria as applicable).
- A trace so severely reduced that remaining width approaches zero is judged as an open even if a copper filament remains.

## Disposition guidance

The decision is repair-versus-scrap, governed by product class and customer requirements:

- **Class 1/2-style product**: a documented jumper-wire or trace-repair per an approved procedure is common practice. The repair must be electrically verified, mechanically staked, and recorded.
- **Class 3-style product**: conductor repairs on the finished board typically require explicit customer or engineering authority approval; absent that, the board is scrapped or returned to the fabricator.
- **Lot action**: because imaging voids and drill strikes repeat at the same coordinate, one confirmed open triggers inspection of the same location on all lot siblings, and electrical test coverage for the lot should be confirmed before shipment.

Never disposition an intermittent or hairline open as "monitor and ship" — thermal cycling in service will finish the break.
