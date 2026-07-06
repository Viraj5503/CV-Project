---
title: "Mouse bite: description, causes, and impact"
defect_class: mouse_bite
doc_type: overview
---
## What it is

A mouse bite is a series of small, rounded notches eaten into the edge of a copper conductor, so the trace edge looks nibbled rather than straight. Unlike an open circuit, copper remains continuous — the conductor still carries signal — but its cross-section is locally reduced. The defect ranges from a single shallow semicircular nick to a cluster of overlapping bites that leave only a thin neck of copper.

## How it forms

Mouse bites are primarily an etching-stage defect. Typical root causes:

- **Localized over-etching** — etchant attacks the conductor edge where the protective resist has lifted slightly, creating scalloped intrusions.
- **Resist edge defects** — particles, bubbles, or developer residue along the resist boundary expose small windows of copper edge to the etchant.
- **Artwork or imaging flaws** — dust on the phototool or LDI artifacts print tiny voids at the conductor edge that etch through.
- **Mechanical damage** — handling scratches or depanelization stress can chip conductor edges in ways that resemble etched bites.

Because the causes are process-related, mouse bites often recur at similar board regions across a lot (for example, near panel edges where resist adhesion is weakest), so a finding on one board warrants a look at its lot siblings.

## Detection and appearance

Under magnification or AOI, a mouse bite appears as one or more concave intrusions into an otherwise straight conductor edge, with the substrate visible inside the notch. The key inspection measurement is the **remaining conductor width** at the narrowest point, compared against the designed minimum width for that trace. Depth of the deepest bite and the length of trace affected are the secondary measurements.

## Functional impact

The concern is a locally reduced cross-section. Consequences scale with severity:

- **Current-carrying capacity** drops at the neck; a heavily bitten power trace can overheat at rated current.
- **Resistance rises** slightly — rarely significant for signals, but relevant for sense lines and controlled-impedance traces, where the width change also perturbs impedance.
- **Reliability risk**: the notch is a stress concentrator. Thermal cycling and vibration can propagate a crack across the remaining neck, converting a cosmetic mouse bite into a field open-circuit failure.

A shallow bite on a wide trace is often acceptable within width-reduction limits; the same bite on a minimum-width trace may be a reject. That judgment is the subject of the acceptability criteria for this defect class.
