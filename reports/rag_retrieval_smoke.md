# RAG retrieval smoke test

Index: `data/chroma` (104 chunks) — real `all-MiniLM-L6-v2` embeddings, class-filtered retrieval (`defect_class` ∈ {class, general}), top-3.

| Query | Top-1 chunk | Score | Also retrieved | Pass |
|---|---|---|---|---|
| How do I repair a missing hole defect on a PCB? | `missing_hole_rework::000` (rework, missing_hole) | 0.659 | `missing_hole_acceptability`, `missing_hole_rework` | ✅ |
| When is a missing hole acceptable on a bare board? | `missing_hole_acceptability::001` (acceptability, missing_hole) | 0.748 | `missing_hole_overview`, `missing_hole_rework` | ✅ |
| How do I repair a mouse bite defect on a PCB? | `mouse_bite_overview::002` (overview, mouse_bite) | 0.640 | `mouse_bite_overview`, `mouse_bite_overview` | ✅ |
| When is a mouse bite acceptable on a bare board? | `mouse_bite_overview::002` (overview, mouse_bite) | 0.618 | `mouse_bite_overview`, `mouse_bite_overview` | ✅ |
| How do I repair a open circuit defect on a PCB? | `open_circuit_rework::000` (rework, open_circuit) | 0.611 | `open_circuit_rework`, `general_rework_practices` | ✅ |
| When is a open circuit acceptable on a bare board? | `open_circuit_overview::004` (overview, open_circuit) | 0.598 | `open_circuit_overview`, `open_circuit_overview` | ✅ |
| How do I repair a short defect on a PCB? | `general_rework_practices::001` (rework, general) | 0.498 | `short_rework`, `short_rework` | ✅ |
| When is a short acceptable on a bare board? | `short_acceptability::003` (acceptability, short) | 0.461 | `short_overview`, `short_overview` | ✅ |
| How do I repair a spur defect on a PCB? | `spur_rework::000` (rework, spur) | 0.702 | `spur_overview`, `general_rework_practices` | ✅ |
| When is a spur acceptable on a bare board? | `spur_acceptability::001` (acceptability, spur) | 0.556 | `spur_overview`, `spur_overview` | ✅ |
| How do I repair a spurious copper defect on a PCB? | `spurious_copper_rework::000` (rework, spurious_copper) | 0.575 | `general_rework_practices`, `spurious_copper_overview` | ✅ |
| When is a spurious copper acceptable on a bare board? | `spurious_copper_rework::000` (rework, spurious_copper) | 0.609 | `spurious_copper_overview`, `spurious_copper_acceptability` | ✅ |

**Result: 12/12 queries passed.**
