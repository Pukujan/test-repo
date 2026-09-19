# Ontology v0 — freeze before inference

## Core top-level labels

The first real-data baseline intentionally uses a small single-label ontology:

- `legal` — statutes, regulations, contracts, case/rule analysis, legal obligations/rights.
- `finance` — accounting, financial statements, markets, banking, investment, financial risk/economics when the financial function is primary.
- `science` — empirical/natural-science research and technical scientific exposition where the scientific subject is primary.
- `technology` — software, computing systems, cybersecurity, developer/IT infrastructure, computer engineering, and applied computing where the technology function is primary.

This is a baseline ontology, not the final production schema.

## Why single-label first

The current experiment is trying to isolate one question: can the Potion student learn the teacher's useful real-domain decision boundary?

Hierarchical and multi-label classification add separate modeling/evaluation problems. Do not add them until this baseline is understood.

## Boundary policy

When an item plausibly spans domains, do not force it into the primary benchmark merely to increase N.

Examples:

- banking regulation: likely `legal + finance`;
- cybersecurity disclosure rule: `legal + finance + technology`;
- computational biology methods: `science + technology`.

These belong in the separately reported mixed-domain challenge slice unless an independent review process supplies a defensible primary label or multi-label gold.

## Freeze artifact

Before inference create `inputs/ontology.json` containing:

- schema/version ID;
- the four labels;
- definitions;
- positive examples;
- negative/boundary examples;
- mixed-domain policy;
- date frozen.

Once baseline inference starts, do not edit ontology definitions in place. A changed ontology requires a new dataset/schema version or a new experiment.
