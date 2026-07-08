# OBn ChromaDB Dimension Mismatch — Diagnosis & Fix

**Date**: 2026-06-23
**Observed in**: OBn sync stdout log

## Symptom

```
✗ Chroma insert failed: Inconsistent dimensions in provided embeddings
```

The sync continues past the error (rc=0 overall), but the affected pod's collection
gets no new embeddings. The pod shows as "failed" in the sync summary.

## Root Cause

The ChromaDB collection was created with an embedding model that produces vectors
of a different dimension than the current model (Ollama `nomic-embed-text`).
This typically happens when:
- The embedding model was changed after collection creation
- A collection was migrated from a different environment
- The Ollama model was updated and now produces different-dimension embeddings

## Fix

1. Identify the affected collection:
   ```python
   import chromadb
   client = chromadb.PersistentClient(path='/Users/jack.reis/.chromadb/obn')
   for c in client.list_collections():
       print(f'{c.name}: {c.count()} docs')
   ```

2. Drop and recreate the affected collection (data will be re-ingested on next sync):
   ```python
   client.delete_collection("collection_name")
   ```

3. Trigger a manual sync or wait for the next launchd cycle (every 30min).

## Prevention

- Pin the embedding model version in the ingest script
- Add a pre-ingest dimension check that compares the model's output dimension
  against the collection's existing dimension before inserting
