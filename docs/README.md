# Vendora architecture & schema exports

Files in this folder:

- `architecture.mmd` — System architecture (Mermaid flowchart)
- `er_diagram.mmd` — Database ER diagram (Mermaid erDiagram)
- `sequence_checkout.mmd` — Checkout sequence diagram
- `sequence_import.mmd` — Product import sequence diagram
- `sequence_ai.mmd` — AI query/response sequence diagram
- `schema.sql` — Simplified SQL DDL generated from Django models

How to render diagrams locally:

1. Install `mermaid-cli` (requires Node.js):

```bash
npm install -g @mermaid-js/mermaid-cli
```

2. Render a file to PNG or SVG:

```bash
mmdc -i docs/architecture.mmd -o docs/architecture.png
mmdc -i docs/er_diagram.mmd -o docs/er_diagram.png
```

Or open the `.mmd` files in https://mermaid.live/ to preview and export.

Notes:
- The `schema.sql` is a simplified DDL to review relationships — adapt types/constraints to your DB.
- If you want me to produce PNG/SVG files here, I can try to render and save them in the repo (may require extra tools).
