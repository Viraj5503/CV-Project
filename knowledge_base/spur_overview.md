---
title: "Spur: description, causes, and impact"
defect_class: spur
doc_type: overview
---
## What it is

A spur is a narrow projection of unwanted copper sticking out from the edge of an otherwise correct conductor or pad — a whisker, point, or tab that remains attached to the feature it grew from. It differs from spurious copper, which is an isolated island with no connection to any conductor, and from a short, where the protrusion completes a bridge to a neighboring net. A spur is attached at one end and free at the other; its significance is how far it intrudes into the clearance gap toward the next conductor.

## How it forms

Spurs are etching-stage artifacts, produced when a small area adjacent to a conductor is protected from the etchant that should have removed it:

- **Resist edge defects** — a fringe, burr, or bubble at the resist boundary shields a filament of copper along the conductor edge.
- **Artwork nicks and dust** — a particle or scratch on the phototool touching a feature outline prints a protrusion attached to it; this repeats identically on every board imaged from that tool.
- **Under-etch at feature corners** — etchant flow is weakest in tight geometry, leaving fillets or points at corners and junctions.
- **Sliver fold-over** — a long thin etching sliver can remain attached at one end, forming a hinged whisker that may move later.

## Detection and appearance

Under AOI or magnification, a spur is a sharp-edged copper projection breaking an otherwise straight feature outline. The two key measurements are the **remaining clearance** between the spur tip and the nearest adjacent conductor, and the spur's own attachment width — a thin neck suggests it can break off. Fine spurs may hide under solder mask; oblique lighting or backlight helps reveal them.

## Functional impact

A spur's threat is mostly prospective rather than immediate:

- **Clearance reduction** — the tip narrows the isolation gap to its neighbor. At higher voltages this invites leakage or arcing; in humid or contaminated environments it seeds electrochemical migration and dendrite growth across the shortened gap.
- **Breakage risk** — a spur with a thin attachment neck can detach during handling, cleaning, or vibration and land elsewhere as loose conductive debris — a latent short at a random location.
- **Signal effects** — on controlled-impedance or RF conductors, a protrusion perturbs the local geometry, though this matters only in sensitive designs.

A short, blunt spur that still leaves the design clearance intact is often acceptable; a sharp filament reaching deep into a minimum clearance is not. That boundary is drawn in the acceptability criteria for this class.
