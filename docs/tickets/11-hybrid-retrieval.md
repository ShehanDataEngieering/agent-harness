# 11 Hybrid retrieval and Citations

**Status:** todo · **Seam:** Session, Retriever · **Depends on:** 10 · **Stories:** 17

## What

Ingest the fictional handbook into Postgres as Clauses (tsvector + pgvector), search with BM25 and vectors merged by RRF, expose search_policy (read), and add the Citation Check.

## Acceptance tests

- [ ] searching for a handbook topic returns the matching Clause first
- [ ] a Citation to a Clause that does not exist fails a Check
- [ ] re-ingesting an unchanged document does not re-embed it
