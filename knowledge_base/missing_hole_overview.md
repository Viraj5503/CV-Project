---
title: "Missing hole: description, causes, and impact"
defect_class: missing_hole
doc_type: overview
---
## What it is

A missing hole is a location where the board design calls for a drilled hole — a plated through-hole for a component lead, a via connecting copper layers, or a non-plated mounting hole — but no hole is present in the fabricated board. The land pattern and annular ring copper are usually present and correctly formed; only the drilled barrel is absent, which makes the defect easy to spot optically as a solid copper pad where a dark hole should be.

## How it forms

Missing holes almost always originate in the drilling stage of fabrication. The most common causes are:

- **Drill program errors** — a coordinate omitted from the NC drill file, or the wrong drill file revision loaded for the job, so the machine never addresses that location.
- **Broken drill bit** — a bit snaps mid-run and the breakage goes undetected, leaving every subsequent hole in that tool's sequence undrilled.
- **Tool table mix-ups** — a diameter mapped to an empty spindle position, so the machine skips all holes assigned to that tool.
- **Registration or clamping faults** — the panel shifts or a re-drill pass is skipped after a tooling stop.

Because these causes are systematic, a single missing hole on one board frequently means the same hole is missing on every board in the panel or lot. A missing-hole finding should always trigger inspection of sibling boards from the same run.

## Detection and appearance

In automated optical inspection the defect appears as an unbroken copper land: the pad is present but shows no drilled aperture and no barrel reflection. On x-ray or electrical test, a missing via shows up as an open between the layers it was meant to join. Missing component holes are often first caught at assembly, when a through-hole part physically cannot be inserted.

## Functional impact

The impact depends on the hole's role. A missing component hole blocks assembly outright — the part cannot be mounted. A missing via breaks the intended interlayer connection, producing an open circuit on that net even though every visible trace is intact. A missing mounting or tooling hole prevents mechanical fastening or downstream fixturing. Unlike cosmetic surface defects, a missing hole is functionally significant in nearly every case, and because plated barrels must be formed during fabrication (drilling, then electroless copper deposition, then electroplating), it is one of the hardest defects to correct outside the fab. Field repair options exist but are limited, which is why disposition frequently favors returning the lot to the fabricator.
