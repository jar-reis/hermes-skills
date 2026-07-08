# Memory SOP Audit (Reference)

**Purpose**: One-shot audit script for L1/L2/L3 memory hygiene.

## Usage
```bash
~/.hermes/bin/memory-prune.sh            # read-only, exits 0/1/2
~/.hermes/bin/memory-prune.sh --fix      # soft-delete L3 duplicates
~/.hermes/bin/memory-prune.sh --json     # machine-readable
```

## Exit Codes
- `0`: Clean
- `1`: Warnings
- `2`: Critical

## Example Output
```json
{
  "l1": {
    "memory_md": {
      "chars": 1760,
      "budget": 2200,
      "percent": 80,
      "anti_patterns": ["commit-SHA"]
    }
  },
  "l2": {
    "status": "UP",
    "last_document_at": "2026-06-18T12:00:00Z"
  },
  "l3": {
    "facts": 97,
    "duplicates": 2
  }
}
```