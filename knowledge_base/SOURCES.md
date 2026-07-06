# Knowledge Base Sources and Licensing

## What this corpus is

The 21 markdown documents in this directory are the retrieval corpus for the
Phase 2 RAG repair advisor. They cover the six defect classes detected by the
Phase 1 model (`missing_hole`, `mouse_bite`, `open_circuit`, `short`, `spur`,
`spurious_copper`) plus cross-cutting `general` topics, with three document
types per class: `overview` (description, causes, impact), `acceptability`
(accept/reject criteria and disposition), and `rework` (repair procedures).

## Authorship and licensing approach

**All documents are self-authored for this project** and released under the
repository's MIT license. They were written from general, publicly documented
PCB fabrication and rework engineering practice — the kind of material found
in rework-equipment manufacturers' application notes and repair guides,
university electronics-manufacturing course material, PCB fabricators' public
capability and quality pages, and industry articles summarizing acceptability
concepts.

**No text was scraped from or reproduced out of copyrighted standards.**
Official standards such as IPC-A-610 (assembly acceptability) and
IPC-7711/7721 (rework and repair) are paywalled, copyrighted documents; this
corpus deliberately does not quote, paraphrase section-by-section, or
reproduce their tables or numeric limits. Where the documents use the
"Class 1 / Class 2 / Class 3" product-class framing or give example numeric
thresholds, these are stated as *self-authored summaries of widely applied
industry practice in the style of* such standards — a framing choice
documented inside each acceptability file.

## Fitness for purpose

These documents exist to demonstrate retrieval-augmented generation with
citations over a domain corpus. They are written to be technically sound, but
they are **not** a certified quality standard and must not be used to make
real production accept/reject decisions. Real dispositions belong to the
applicable customer drawing and the current revision of the official
standards, applied by qualified inspectors.

## Document inventory

| Class | overview | acceptability | rework |
|---|---|---|---|
| missing_hole | `missing_hole_overview.md` | `missing_hole_acceptability.md` | `missing_hole_rework.md` |
| mouse_bite | `mouse_bite_overview.md` | `mouse_bite_acceptability.md` | `mouse_bite_rework.md` |
| open_circuit | `open_circuit_overview.md` | `open_circuit_acceptability.md` | `open_circuit_rework.md` |
| short | `short_overview.md` | `short_acceptability.md` | `short_rework.md` |
| spur | `spur_overview.md` | `spur_acceptability.md` | `spur_rework.md` |
| spurious_copper | `spurious_copper_overview.md` | `spurious_copper_acceptability.md` | `spurious_copper_rework.md` |
| general | `general_bareboard_process_defects.md` | `general_inspection_criteria.md` | `general_rework_practices.md` |

Frontmatter contract (used by `pcb_vision.rag.ingest`): every retrieval
document carries `title`, `defect_class` (one of the six classes or
`general`), and `doc_type` (`overview` | `acceptability` | `rework`). This
file is excluded from ingestion.
