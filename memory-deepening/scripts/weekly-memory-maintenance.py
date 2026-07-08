# Weekly Memory Maintenance Script

**Purpose**: Prune L1, deduplicate L3, and distill L4 (ContextForge).

## Code
```python
#!/usr/bin/env python3
import subprocess
from hermes_tools import mcp_contextforge_memory_query, mcp_contextforge_memory_delete_batch

def weekly_maintenance():
    subprocess.run(["~/.hermes/bin/memory-prune.sh", "--fix"], check=True)
    
    stale_items = mcp_contextforge_memory_query(
        query="older_than:30d AND NOT tags:durable",
        limit=50
    )
    if stale_items.get("results"):
        mcp_contextforge_memory_delete_batch(
            filter={"ids": [item["id"] for item in stale_items["results"]]},
            dry_run=False
        )
    
    return "Weekly maintenance complete."

if __name__ == "__main__":
    print(weekly_maintenance())
```