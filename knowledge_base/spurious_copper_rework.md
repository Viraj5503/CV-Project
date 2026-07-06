---
title: "Spurious copper: rework and repair procedure"
defect_class: spurious_copper
doc_type: rework
---
## Repair feasibility

Spurious copper removal is a subtractive repair with excellent success rates: the island is not part of any circuit, so taking it off restores the designed bare-laminate region without touching a single functional conductor. The risks are collateral only — scratching the laminate deeply enough to expose glass fibers, damaging the solder mask of neighboring traces, or losing the removed flake onto another part of the board. Feasibility is genuinely limited only when the island is trapped under features that cannot be disturbed or embedded so deeply (pressed-in swarf) that extraction would gouge the substrate; such boards are dispositioned rather than reworked.

## Tools and materials

- Stereo microscope or bench magnifier (10x or better)
- Curved scalpel or flat micro-chisel blade; fine tweezers
- Fiberglass scratch brush for thin films and residue
- Isopropyl alcohol, lint-free wipes; tape or tack putty to capture flakes
- Repair-grade solder mask or lacquer if the surrounding mask is opened
- Multimeter for isolation spot-checks in tight clearance regions

## Procedure

1. **Characterize the island**: confirm from the artwork that the copper is genuinely spurious (not an intentional pour, thieving pad, or fiducial — copper thieving patterns look exactly like random islands but are deliberate). Measure its clearance to neighbors and probe adhesion gently.
2. **Protect the neighborhood**: mask adjacent conductors with tape if the island sits in a dense region, so a slipped blade meets tape instead of trace.
3. **Lift the island**: slide the blade flat under one edge of the patch and peel it up in a single piece where possible. Thin etch films respond better to the fiberglass brush; abraded material must be brushed toward and onto a piece of tape, never across the board.
4. **Extract embedded swarf**: pressed-in metallic debris is picked out with the blade tip at a shallow angle. Stop if extraction starts tearing laminate — a board gouged to the glass weave has traded one defect for another and goes back to disposition.
5. **Capture and clean**: secure the removed copper on tape immediately, then IPA-clean the area and inspect for any remaining slivers or residue.
6. **Restore the surface**: if solder mask was cut or the laminate is exposed and the region requires insulation, re-coat with repair mask or lacquer.

## Post-repair inspection

Under magnification, confirm the designed clearance region is fully clear, neighboring conductors and their mask are undamaged, and no laminate gouge exposes glass fibers (light surface scuffing is normal; visible weave is not). Spot-check isolation between the conductors flanking the removal site in minimum-clearance areas. Log location, island size, removal method, operator, and date. If the island matched the artwork-spot pattern — same coordinate expected on lot siblings — flag the lot for screening and the phototool for cleaning, because the rework fixed this board only.
