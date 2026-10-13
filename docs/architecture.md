# Vendora System Architecture

This document contains a human-readable system architecture diagram for the Vendora project. The original Mermaid source is in `docs/architecture.mmd`.

## Overview

- Users access the `vendora` Django web application via browser (HTTP/HTTPS).
- The Django app routes requests via `vendora.urls` to app-specific URL modules.
- Core apps: `accounts`, `products`, `orders`, `companies`, `cart`, `dashboard`, `reports`, `ai_assistant`.
- Storage: relational database (Postgres/MySQL/SQLite), `ai_embeddings/product_index.faiss`, and uploaded media under `media/`.
- Background scripts such as `products_import.py` populate DB and build FAISS embeddings.
- External services: payment gateway and email/SMS provider.

## Mermaid (flowchart)

```mermaid
flowchart LR
  Browser[User Browser]
  Browser -->|HTTP/HTTPS| WebServer[vendora (Django) Web App]
  WebServer -->|URL dispatch| URLConf[vendora.urls -> app urls]
  WebServer -->|WS/HTTP| Apps{Django Apps}
  Apps --> Accounts[accounts]
  Apps --> Products[products]
  Apps --> Orders[orders]
  Apps --> Companies[companies]
  Apps --> Cart[cart]
  Apps --> Dashboard[dashboard]
  Apps --> Reports[reports]
  Apps --> AI[ai_assistant]
  WebServer --> Templates[templates/static]
  WebServer --> Media[media/ uploads]
  WebServer -->|ORM (Django ORM)| DB[(Database: Postgres/MySQL/SQLite)]
  AI -->|uses| FAISS[ai_embeddings/product_index.faiss]
  AI -->|reads| AIJSON[ai_training_data.json]
  Scripts[products_import.py & scripts/products_import.py] -->|populate| DB
  Scripts -->|create embeddings| FAISS
  Admin[Admin Interface]
  WebServer --> Admin
  PaymentGateway[(External Payment Gateway)]
  WebServer -->|payment API| PaymentGateway
  EmailSMS[(Email/SMS Provider)]
  WebServer -->|mailer| EmailSMS
  CI[management scripts / manage.py]
  CI --> WebServer
  
  subgraph Storage
    DB
    FAISS
    Media
  end
  
  Browser -->|uploads| Media
  Browser -->|fills forms| WebServer
  
  note right of AIJSON: "Training & knowledge files (ai_training_data.json)"
  note right of FAISS: "Vector index used by ai_assistant for semantic search"
```

## Notes
- Open `docs/architecture.mmd` in a Mermaid-capable viewer (e.g., https://mermaid.live/) to export PNG/SVG.
- See `docs/README.md` for rendering instructions.
