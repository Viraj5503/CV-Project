---
title: "Mouse bite: rework and repair procedure"
defect_class: mouse_bite
doc_type: rework
---
## Repair feasibility

A mouse bite within acceptance limits should not be reworked at all — the conductor is compliant, and any added material or heat only introduces new risk. Rework applies to bites that reduce conductor width beyond the class limit but leave the trace otherwise intact. The goal is to restore current-carrying cross-section and mechanically reinforce the weakened neck. Two established techniques exist: a **solder bridge reinforcement** over the notch for modest reductions, and a **lap-soldered wire strap** for severe reductions or clustered bites. Both are surface repairs; neither restores the board to as-fabricated condition, so class rules and customer approval govern whether they are permitted.

## Tools and materials

- Stereo microscope or bench magnifier (10x or better) with oblique lighting
- Fiberglass scratch brush or curved scalpel for mask removal and edge cleanup
- Liquid no-clean or RMA flux, wire solder, temperature-controlled iron with fine chisel tip
- For straps: bare or pre-tinned copper ribbon / 30 AWG wire, cut slightly longer than the damaged span
- Isopropyl alcohol and lint-free wipes; repair-grade solder mask or conformal lacquer for resealing

## Procedure

1. **Confirm the repair is warranted**: measure remaining width at the deepest notch and check it against the acceptability criteria; record the measurement.
2. **Prepare the site**: gently remove solder mask from the conductor for 2–3 mm on each side of the notch, exposing bright copper. Clean with IPA and apply flux.
3. **For a modest reduction (solder reinforcement)**: tin the exposed span so solder wets across the notch, filling the missing cross-section with a smooth, continuous fillet. Avoid blobs — the fillet should follow the trace profile.
4. **For a severe reduction or cluster (wire strap)**: tin the exposed copper each side, lay the copper strap along the trace so it spans the entire damaged region, and lap-solder both ends and the middle so the strap is bonded along its length, not just at the tips.
5. **Reseal**: clean flux residue, then re-cover the repair with repair mask or lacquer to restore insulation and mechanical protection.

## Post-repair inspection

Verify continuity end-to-end on the net and confirm no solder has bridged to adjacent conductors (check clearance under magnification, and electrically on fine-pitch regions). Confirm the repair is smooth, wetted, and free of cold-joint dullness. Log location, technique, operator, and measurements in the rework record, and route the board through normal electrical test before release.
