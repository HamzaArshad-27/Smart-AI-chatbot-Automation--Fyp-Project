# Vendora SQL Schema (Readable)

A simplified SQL schema is exported to `docs/schema.sql`. Use it as a reference to understand tables and relationships.

## How to inspect

- Open `docs/schema.sql` in an editor or run it (after review) in a database to create schema skeleton.
- Example to run in Postgres (replace DB/credentials):

```bash
psql -h localhost -U postgres -d vendora_db -f docs/schema.sql
```

## Important notes

- The DDL is simplified: adjust types, constraints, indices, and `ON DELETE` rules for your production DB.
- Use Django migrations (`manage.py makemigrations` / `manage.py migrate`) in normal development; this DDL is for review/export only.
