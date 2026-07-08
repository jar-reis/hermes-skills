---
name: cited-recall
title: Cited Recall with Abstention
description: Multi-source memory recall that synthesizes a cited answer with explicit abstention when evidence is insufficient. Use when the user needs a direct synthesized answer with citations rather than raw chunk dumps.
icon: 📚
tags: [recall, synthesis, abstention, memory, rrf, multi-source]
author: Hermes
version: 1.1
metadata:
  hermes:
    tags: [recall, synthesis, abstention, memory, rrf, multi-source]
    related_skills: [memory-sop, turn-sync, enrich-memory]
---

# Cited Recall with Abstention

## When to Use Cited Recall vs. Raw Search

### **Use Cited Recall When:**
- The user asks for a **direct, synthesized answer** (e.g., "What did we decide about X?", "How do I do Y?").
- The answer will be **user-facing** (e.g., displayed in a dashboard, shared in a report, or surfaced in a chat).
- You need **citations** to back up the answer (e.g., "According to [OB1], we chose Postgres because...").
- You want to **explicitly abstain** when confidence is low (e.g., "No answer available: insufficient sources or low relevance scores").

### **Use Raw Search When:**
- The agent is **exploring internally** (e.g., gathering context for a task, debugging, or verifying facts).
- The user explicitly requests **raw chunks** (e.g., "Show me all notes about X").
- You need **unfiltered results** for further processing (e.g., feeding into another tool or skill).

---

## Multi-Source Query Pattern

Cited recall follows a **tiered recall strategy** to balance speed and coverage:

1. **Tier 0: Context** (MEMORY.md or in-context notes)
   - Check if the answer is already in the current context (e.g., MEMORY.md or recent notes).
   - If found, return it immediately with a citation to the source.

2. **Tier 1: OB1** (High-confidence, curated knowledge)
   - Query OB1 (Supabase pgvector) for high-relevance chunks.
   - Use a **minimum score threshold of 0.5** to filter results.

3. **Tier 2: OBn + Session** (Federated local knowledge)
   - Query OBn (federated ChromaDB pods) and session memory for additional context.
   - Combine results with OB1 and deduplicate.

4. **Tier 3: Honcho + Hindsight** (Reasoning and durable memory)
   - Query Honcho (reasoning layer) and Hindsight (PostgreSQL-backed durable memory) for low-confidence or long-tail knowledge.
   - Use these results to **augment** the answer, not replace higher-tier sources.

### Actual Adapters in `cited_recall.py`

| Source | Adapter Function | Interface | Auth |
|---|---|---|---|
| OB1 | `query_ob1()` | Supabase REST API (`/rest/v1/rpc/search_thoughts`) | Token from `~/.hermes/bin/ob1-token.sh` |
| OBn | `query_obn()` | ChromaDB at `localhost:8001/api/v1/search` | Local (no auth) |
| Session | `query_session()` | SQLite FTS5 on `~/.hermes/state.db` | Local (filesystem) |
| Hindsight | `query_hindsight()` | HTTP at `localhost:8888/search` | Local (no auth) |
| memory_store | `query_memory_store()` | SQLite FTS5 on `~/.hermes/memory_store.db` (facts_fts table) | Local (filesystem) |

All adapters run in parallel via `ThreadPoolExecutor(max_workers=5)`. Each returns `(chunks, error)` — errors are logged but don't fail the pipeline.

---

## Reranking Strategy

After gathering results from all tiers:

1. **Deduplicate** chunks by content hash (MD5 of content, first 12 chars). When two chunks share a hash, keep the higher-scored one.
2. **Rerank** using **Reciprocal Rank Fusion (RRF)** with source priority weighting:
   - Raw RRF score: `Σ (1 / (k + rank_i(d)))` where k=60 and rank_i is the chunk's 1-indexed rank within its source.
   - Multiply by source priority weight: OB1=1.0, OBn=0.9, Hindsight=0.8, session=0.7, Honcho=0.6, memory_store=0.5.
   - **Normalize** RRF scores to 0–1 range by dividing by the max raw score. This is critical — raw RRF scores are tiny (e.g., 0.016) and won't pass any reasonable threshold without normalization.
3. **Filter** chunks with a normalized RRF score **< 0.3**.
4. **Sort** remaining chunks by score in descending order.
5. **Assign citation IDs** (1-indexed) after sorting.

---

## Synthesis Prompt Template

Use the following prompt to synthesize a cited answer from the reranked chunks:

```
You are an expert synthesizer. Your task is to answer the user's query using the provided context from memory stores. Follow these rules strictly:

1. Be concise: Answer in 2-3 sentences. Use bullet points only if necessary.
2. Cite sources: Use inline citations like [1], [2], etc., where [N] corresponds to the source ID in the context.
3. Abstain if unsure: If the context is insufficient or relevance scores are low, respond with exactly: "NO_ANSWER_AVAILABLE: <reason>"
4. Do not hallucinate or infer beyond the provided evidence.
5. Prioritize high-confidence sources (OB1, OBn) over lower ones (session, memory_store).

Query: {query}

Context (ranked by relevance):
{context}

Answer:
```

### LLM Fallback Chain

1. **Hermes API** (`http://127.0.0.1:8642/v1/chat/completions`) — primary, uses the configured Hermes model
2. **Ollama** (`http://127.0.0.1:11434/api/generate`) — fallback, uses `qwen2.5:7b` by default
3. **No LLM** — returns reranked chunks without synthesis with a note that LLM was unavailable

If the LLM returns `NO_ANSWER_AVAILABLE: <reason>`, the pipeline abstains with that reason.

---

## Abstention Rule

Abstain from synthesizing an answer if **ANY** of these conditions are true:

| Condition | Threshold | Reason Text |
|---|---|---|
| No results from any source | `total_results == 0` | "No results from any memory store." |
| Fewer than 2 sources return results | `sources_with_results < 2` | "Insufficient sources (N < 2). Only one source returned results." |
| Top RRF score below minimum | `top_score < 0.3` | "Low relevance scores (top RRF score: X < 0.3)." |
| Fewer than 2 total chunks | `total_results < 2` | "Insufficient evidence (N < 2 chunks)." |
| LLM explicitly abstains | `NO_ANSWER_AVAILABLE` in response | LLM-provided reason |

**Abstention still populates citations** — the user can see what was found even when no synthesis was produced.

---

## How to Invoke `cited_recall.py`

### **From Any Agent**

1. **Command:**
   ```bash
   python3 ~/.hermes/scripts/cited_recall.py --query "Your query here" [--html] [--json] [--output path]
   ```

2. **Flags:**
   - `--query` / `-q` (required): The query string
   - `--limit` / `-l` (default 5): Max results per source
   - `--html`: Output a self-contained dark-themed HTML report
   - `--json`: Output JSON (default if neither --html nor --json specified)
   - `--output` / `-o`: Output file path (default: stdout for JSON, `cited_recall_output.html` for HTML)

3. **Output structure (JSON):**
   ```json
   {
     "query": "...",
     "synthesized_answer": "...",
     "abstained": false,
     "abstention_reason": null,
     "citations": [{"citation_id": 1, "source_type": "ob1", "content": "...", "rrf_score": 1.0, ...}],
     "sources": {"ob1": {"count": 2, "max_score": 0.85, "avg_score": 0.8}, ...},
     "chunks": [...],
     "errors": ["hindsight: HTTP Error 404: Not Found", ...],
     "timestamp": "2026-06-22T22:04:16Z"
   }
   ```

---

## Pitfalls

### RRF Scores Need Normalization
Raw RRF scores are extremely small (e.g., `1/(60+1) * 1.0 = 0.0164`). Without normalizing to 0–1, any threshold like 0.3 will reject everything. The implementation normalizes by dividing all scores by the max raw score.

### Session FTS5 Returns Raw Tool-Call JSON
The session DB (`~/.hermes/state.db`) stores message content as raw text, which often includes serialized JSON from tool calls. This means session search results can be large, noisy, and hard for the LLM to synthesize. A future improvement would add a content extractor that strips tool-call JSON and keeps only human-readable text.

### OB1 Token Path
The OB1 adapter expects `~/.hermes/bin/ob1-token.sh` to export an `OB1_API_KEY` environment variable. If the script is missing or the token is expired, OB1 queries silently fail with "no API key available." Check token freshness before relying on OB1 results.

### OBn and Hindsight Endpoints May Be Down
OBn (localhost:8001) and Hindsight (localhost:8888) are local services that may not always be running. The pipeline handles this gracefully (logs the error, continues with other sources), but you'll get more complete results when all services are up.

### Subagent-Generated Skills Need Verification
This skill was initially created by a parallel subagent. The subagent's version had the abstention threshold wrong (0.5 instead of 0.3) and lacked RRF normalization detail, the actual adapter list, and the pitfalls section. Always verify subagent-generated artifacts against the real implementation.

---

## Notes
- Design brief: `~/.hermes/plans/cited-recall-layer/design-brief.md`
- API reference (full): `references/api-reference.md` — structured per-interface reference with auth, rate limits, and live-test status
- API reference (canonical path): `~/.hermes/plans/cited-recall-layer/api-reference.md`
- Tests: `~/.hermes/scripts/tests/test_cited_recall.py` — 15/15 passing
- Origin: Closes the "cited-answer-with-abstention recall layer" gap from the Simon Scrapes memory system video analysis (2026-06-12). The other gap (per-turn capture density) was closed by the turn-sync protocol on 2026-06-19.
- Prism agent reference: `references/prism-agent-cited-canvas-pattern-20260627.md` — historical example of the agent-side mirror of cited-recall (Khoj's Prism forced inline citations on every claim, 2026-04-15).