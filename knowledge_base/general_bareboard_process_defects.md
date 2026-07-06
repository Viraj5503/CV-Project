---
title: "How bare-board fabrication stages map to defect types"
defect_class: general
doc_type: overview
---
## Why process mapping matters

Each defect class in this knowledge base is the fingerprint of a specific fabrication stage. Reading a defect back to its stage tells you three things: whether it will repeat across the lot (tooling faults repeat at identical coordinates; chemistry faults cluster by panel region), what the fabricator must fix at the source, and how much to trust the rest of the board. An inspector who knows the process reads a board like a log file.

## Imaging: where artwork flaws become copper flaws

The conductor pattern is defined by exposing photoresist through a phototool (or by laser direct imaging). Anything wrong with the image prints onto every board made from it: an opaque dust particle bridging two features prints copper where the etchant should have cleared — a **short** or **spur**; a particle sitting alone in a clearance area prints an isolated island — **spurious copper**; a transparent void or scratch in a feature exposes resist that should have been protected, so the etch removes conductor — an **open circuit** or the edge notching seen as **mouse bite**. Imaging defects are the great repeaters: the same flaw at the same coordinate, board after board, until the tool is cleaned or remade.

## Etching: the balance that decides most pattern defects

Etching removes every square millimeter of copper the resist does not protect, and its two failure directions produce opposite defects. **Under-etch** (weak chemistry, poor agitation, insufficient time) leaves copper behind: webs bridging clearances (**short**), points and whiskers on feature edges (**spur**), and residual films or islands (**spurious copper**). **Over-etch** attacks protected features from the sides: conductor edges scallop and neck down (**mouse bite**), and fine traces sever entirely (**open circuit**). Because both directions flow from bath control, etch-signature defects usually scatter across a panel region rather than repeating at one coordinate — a distribution clue that separates them from imaging faults.

## Drilling: mechanical faults with digital causes

Holes are drilled by NC machines executing a drill file. A coordinate missing from the program, a broken bit that goes undetected, or a tool-table mix-up produces the **missing hole** — no barrel where the design demands one. Drilling also produces secondary damage that mimics other classes: a mis-registered hit that clips a conductor creates an **open circuit**, and drilling swarf pressed into the laminate reads as **spurious copper**. Drill faults are tooling faults: expect the identical omission on every board in the run.

## Plating and beyond

Electroless deposition and electroplating give through-holes their conductive barrels and thicken the pattern. Thin or cracked plating at a trace-to-pad knee surfaces later as an intermittent **open circuit**; plating nodules and overgrowth can close clearances toward a **short**. Downstream, solder-mask and surface-finish stages rarely create pattern defects but routinely **hide** them — which is why marginal visual findings are settled electrically, and why a clean AOI pass on a masked board is not an isolation guarantee.

## Reading a board like a log file

Two habits turn this map into practice. First, classify by distribution: same-coordinate repetition across boards means tooling (imaging, drill program); regional clustering on the panel means chemistry (etch, development, plating). Second, remember that one root cause seeds many symptoms: a single dirty phototool can simultaneously explain a short on one board, spurs on another, and spurious copper on a third. The defect classes are separate labels for inspection, but they are neighbors in the process — and dispositions, lot screens, and fab feedback should treat them that way.
