---
title: "Open circuit: rework and repair procedure"
defect_class: open_circuit
doc_type: rework
---
## Repair feasibility

Open circuits are among the most repairable PCB defects when the break is on an outer layer: the two ends of the conductor are accessible, and a bridging repair restores the net. Feasibility drops sharply for inner-layer opens (no access without destructive excavation — normally scrap) and for opens in controlled-impedance or RF paths, where a repair restores continuity but not the designed impedance. Three techniques cover outer-layer cases, chosen by gap length: **solder bridging** for hairline breaks, a **lap-soldered wire or ribbon** for gaps up to several millimeters, and a **pad-to-pad insulated jumper** when the damaged span is long or the trace route is congested.

## Tools and materials

- Stereo microscope (10x+), fiberglass brush, curved scalpel
- Temperature-controlled iron with fine tip, wire solder, liquid flux, IPA and wipes
- Bare copper ribbon or 30 AWG bare wire for short straps; 30 AWG insulated (Kynar-type) wire for point-to-point jumpers
- Adhesive or staking lacquer, repair-grade solder mask
- Multimeter for continuity and isolation checks; netlist or schematic for routing jumpers

## Procedure

1. **Characterize the break**: locate both ends under magnification, measure the gap, and confirm the net's endpoints from the netlist. Check the same coordinate on lot siblings.
2. **Prepare the site**: scrape solder mask back to bright copper 2–3 mm beyond each break end. Clean with IPA, apply flux, and tin both exposed ends.
3. **Hairline break (solder bridge)**: flow a smooth solder fillet across the tinned gap so it wets both ends continuously. Suitable only when the gap is a fraction of the trace width.
4. **Short gap (wire/ribbon strap)**: cut a strap overlapping each end by at least 2 mm, hold it aligned along the original trace route, and lap-solder each end. The strap must lie flat and follow the board surface.
5. **Long gap (insulated jumper)**: route 30 AWG insulated wire between the nearest accessible pads or test points on the same net, keeping the run short, flat, and clear of board edges and mounting holes. Solder both terminations and stake the wire to the board every 10–15 mm with lacquer or adhesive.
6. **Reseal**: clean all flux residue and re-cover exposed copper with repair mask.

## Post-repair inspection

Confirm end-to-end continuity on the repaired net and isolation to physically adjacent nets with a multimeter. Inspect solder joints for full wetting and smooth fillets; tug-test jumpers gently before staking cures. Record gap length, technique, materials, operator, and date in the rework log, then route the board through standard electrical test — a repaired open must pass the same test coverage as an undamaged board before release.
