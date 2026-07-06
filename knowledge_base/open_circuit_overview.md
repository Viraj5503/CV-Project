---
title: "Open circuit: description, causes, and impact"
defect_class: open_circuit
doc_type: overview
---
## What it is

An open circuit is a complete interruption in a conductor: the copper trace is physically broken, leaving a gap so that current cannot flow along the intended net. It differs from a mouse bite, where copper is narrowed but continuous — an open has zero remaining cross-section at the break. The gap can be a hairline fracture barely visible at magnification or a missing trace segment several millimeters long.

## How it forms

Opens originate at several fabrication stages, and the appearance hints at the cause:

- **Over-etching** — etchant undercuts a fine trace until it separates; the break edges look tapered and irregular.
- **Resist damage before etch** — a scratch or particle across the resist exposes the trace beneath, which the etchant then removes; the break often has a clean, linear shape matching the scratch.
- **Imaging voids** — dust or bubbles on the phototool print a void in the resist, etching a gap at that exact spot on every board imaged with that tool.
- **Plating folds and thin knees** — in pattern-plated boards, thin plating at a trace-to-pad junction can crack open during thermal stress.
- **Mechanical damage** — handling gouges, depaneling stress, or a mis-set drill striking a trace can sever it after etch.

Tool-related causes (imaging voids, drill strikes) repeat at the same coordinate across the lot, so lot screening is warranted after any confirmed open.

## Detection and appearance

Optically, an open appears as a visible gap in the conductor with laminate showing through, or as a hairline crack that may need oblique lighting to catch. Electrical test finds opens definitively: the net fails continuity between its endpoints. AOI systems flag opens by comparing the etched pattern against the reference artwork; hairline opens that AOI misses are typically caught by flying-probe or bed-of-nails test.

## Functional impact

An open is functionally decisive: the affected net simply does not work. There is no partially-working state to weigh — any circuit depending on that connection fails outright. For this reason, an open circuit is a reject condition in every product class, and the practical question is never whether the board is acceptable as-is, but whether a documented repair (typically a jumper wire or trace-section replacement) is permitted for the product class, or whether the board is scrapped. Hairline opens deserve particular respect: one that intermittently closes at room temperature can pass a bench test and still fail in the field under thermal expansion.
