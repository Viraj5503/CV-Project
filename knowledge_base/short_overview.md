---
title: "Short circuit: description, causes, and impact"
defect_class: short
doc_type: overview
---
## What it is

A short is an unintended copper connection bridging two conductors that the design requires to be electrically isolated — two adjacent traces, a trace and a pad, or a trace and a copper pour. The bridge may be a full-width web of copper, a thin sliver spanning the clearance gap, or a barely-visible filament. Whatever its size, it electrically merges two nets that must remain separate.

## How it forms

Shorts are predominantly an imaging-and-etching defect, the mirror image of the over-etch problems that cause opens:

- **Under-etching** — etchant fails to clear the full clearance channel between conductors, leaving a residual copper web. Common where clearances are at the process minimum or etchant flow is locally restricted.
- **Photoresist scumming** — incompletely developed resist remains in the clearance area and protects copper that should have been removed.
- **Artwork defects** — a dust particle or scratch on the phototool that bridges two features prints as copper on every board imaged from that tool.
- **Copper slivers** — a thin ribbon of copper left by marginal artwork peels partially, folds over, and lands across a clearance.
- **Plating anomalies** — in pattern plating, nodules or overgrowth can expand a feature into its neighbor's clearance.

Tool-driven causes repeat at identical coordinates across a lot; chemistry-driven causes cluster in regions of the panel where flow or exposure is marginal. Either way, one confirmed short justifies screening lot siblings.

## Detection and appearance

Optically, a short shows as copper occupying the gap between two features, often duller or narrower than the neighboring conductors. Fine filament shorts hide under solder mask and may only be found electrically: isolation (leakage) testing between adjacent nets flags them definitively. AOI catches geometric bridges by artwork comparison; flying-probe or grid test catches the electrical ones AOI misses.

## Functional impact

A short is functionally decisive in the same way an open is: two nets that must be independent are now one. Consequences range from immediate hard failure (power rail to ground: excessive current, heat, possible burn damage at power-up) to subtle malfunction (signal-to-signal short causing logic contention or crosstalk that appears intermittently). A resistive filament short is the most treacherous — it may read as a few ohms or kilo-ohms, pass casual inspection, degrade circuit behavior unpredictably, and then weld solid or burn open in service. A short between isolated nets is a reject condition in every product class; the open question is only whether removal by rework is permitted.
