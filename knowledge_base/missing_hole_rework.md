---
title: "Missing hole: rework and repair procedure"
defect_class: missing_hole
doc_type: rework
---
## Repair feasibility

A missing hole is among the least field-repairable PCB defects. The obstacle is plating: production through-holes get their conductive barrel from electroless copper deposition followed by electroplating, which cannot be replicated at a rework bench. Drilling a new hole locally produces bare laminate walls with no layer-to-layer connection. Feasibility therefore depends on the hole's function: missing **non-plated** mechanical holes are drillable; missing **plated** component holes or vias usually mean return-to-fab, with a jumper-wire workaround as the fallback where the design tolerates it.

## Tools and materials

- Precision drill press or PCB rework drill with carbide bits (never freehand a laminate hole)
- Board fixturing and backing material to prevent exit-side burring
- Optical comparator or calipers to locate the hole from the drill drawing datum
- 30 AWG insulated jumper wire, flux, and solder for connectivity workarounds
- Continuity tester or multimeter for post-repair verification

## Procedure

For a missing **non-plated mechanical hole** (low-class product, documented approval):

1. Confirm the hole location and diameter against the current drill drawing.
2. Fixture the board flat with sacrificial backing; mark the location with an optical aid, never by eye.
3. Drill at the specified diameter in a single pass at moderate speed to avoid tearing glass fibers.
4. Deburr both sides lightly and inspect for haloing or delamination around the new hole.

For a missing **via** where the net must be restored without the barrel:

1. Identify the two points the via was meant to connect using the board netlist.
2. Route a 30 AWG insulated jumper between the nearest accessible pads or exposed trace points on each layer's net.
3. Solder both ends with minimal heat, stake the wire to the board surface with adhesive or lacquer, and keep the route short and away from board edges.

For a missing **plated component hole**, do not attempt local drilling — disposition the board for return to the fabricator.

## Post-repair inspection

Verify drilled holes for correct diameter, position, and absence of delamination or measling around the hole wall. For jumper repairs, confirm continuity across the restored net, confirm isolation from adjacent nets, and record the repair location, method, and operator in the board's rework log. Re-inspect after any subsequent assembly step that heats the area.
